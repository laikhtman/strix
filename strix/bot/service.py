import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Optional

from aiohttp import ClientSession, web
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .config import TelegramBotConfig
from .control_api import ControlAPI
from .state import BotState

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 45 * 1024 * 1024  # stay under Telegram limit with buffer
MAX_LIST_ITEMS = 12
MAX_MESSAGE_CHARS = 3500
SEVERITY_LEVEL = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
SEVERITY_ICON = {"critical": "🔥", "high": "🔴", "medium": "🟠", "low": "🟢", "info": "ℹ️"}
BATCH_INTERVAL_SECONDS = 5.0
REDACT_PATTERNS = [("sk-", 3)]


def _is_allowed(user_id: int, config: TelegramBotConfig) -> bool:
    return user_id in config.allowlisted_user_ids


def fetch_tail_page(control_api: ControlAPI, run_id: str, offset: int, page_size: int) -> tuple[list[str], bool, int]:
    """Return a page of logs, whether more remain, and the next offset."""
    logs = control_api.tail_logs(run_id, offset=offset, limit=page_size + 1)
    has_more = len(logs) > page_size
    page = logs[:page_size]
    next_offset = offset + len(page)
    return page, has_more, next_offset


class RateLimiter:
    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self.min_interval = min_interval_seconds
        self.last_seen: dict[int, float] = {}

    def allow(self, user_id: int) -> bool:
        now = time.monotonic()
        last = self.last_seen.get(user_id, 0.0)
        if now - last < self.min_interval:
            return False
        self.last_seen[user_id] = now
        return True


class GlobalRateLimiter:
    def __init__(self, min_interval_seconds: float = 0.5) -> None:
        self.min_interval = min_interval_seconds
        self.last_seen = 0.0

    def allow(self) -> bool:
        now = time.monotonic()
        if now - self.last_seen < self.min_interval:
            return False
        self.last_seen = now
        return True


class Metrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.errors: dict[str, int] = {}
        self.latencies_ms: list[float] = []

    def inc(self, name: str) -> None:
        self.counters[name] = self.counters.get(name, 0) + 1

    def error(self, name: str) -> None:
        self.errors[name] = self.errors.get(name, 0) + 1

    def add_latency(self, ms: float) -> None:
        self.latencies_ms.append(ms)


class AlertSink:
    def __init__(self, webhook: str | None = None) -> None:
        self.webhook = webhook

    async def notify(self, kind: str, details: dict[str, Any]) -> None:
        if not self.webhook:
            return
        payload = {"kind": kind, "details": details, "ts": time.time()}
        try:
            async with ClientSession() as session:
                await session.post(self.webhook, json=payload, timeout=5)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to send alert kind=%s", kind)


def create_dispatcher(control_api: ControlAPI, config: TelegramBotConfig) -> Dispatcher:
    dp = Dispatcher()
    rate_limiter = RateLimiter(min_interval_seconds=config.rate_limit_seconds)
    global_limiter = GlobalRateLimiter(min_interval_seconds=config.global_rate_limit_seconds)
    metrics = Metrics()
    alert_sink = AlertSink(config.alert_webhook)
    dp.metrics = metrics  # type: ignore[attr-defined]
    state = BotState(config.db_path)

    run_verbosity: dict[str, str] = {}
    run_batches: dict[str, list[str]] = {}
    batch_tasks: dict[str, asyncio.Task[Any]] = {}
    doc_hint_ts: dict[int, float] = {}

    def redact(text: str) -> str:
        masked = text
        for prefix, visible in REDACT_PATTERNS:
            idx = masked.find(prefix)
            while idx != -1:
                end = idx + len(prefix) + 16
                masked = masked[: idx + visible] + "***REDACTED***" + masked[end:]
                idx = masked.find(prefix, end)
        return masked

    dp["redact"] = redact

    def format_alert(sev: str, title: str, content: str) -> str:
        icon = SEVERITY_ICON.get(sev, "ℹ️")
        text = f"{icon} *{sev.upper()}* {title}\n```\n{content}\n```"
        if len(text) > MAX_MESSAGE_CHARS:
            text = text[:MAX_MESSAGE_CHARS] + "\n\n(truncated)"
        return text

    def build_file_kb(run_id: str, files: list[dict[str, Any]], rel_path: str = "") -> list[list[InlineKeyboardButton]]:
        kb_rows: list[list[InlineKeyboardButton]] = []
        if rel_path:
            parent = os.path.normpath(os.path.join(rel_path, ".."))
            kb_rows.append(
                [
                    InlineKeyboardButton(
                        text="⬆️ ..",
                        callback_data=f"file_nav:{run_id}:{'' if parent == '.' else parent}",
                    )
                ]
            )
        for entry in files[:MAX_LIST_ITEMS]:
            label = ("D " if entry.get("is_dir") else "F ") + entry.get("name", "")
            entry_rel = entry.get("path", "")
            action = "file_nav" if entry.get("is_dir") else "file_dl"
            kb_rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=f"{action}:{run_id}:{entry_rel}",
                    )
                ]
            )
        return kb_rows

    async def maybe_doc_hint(message: Message, topic: str = "troubleshooting") -> None:
        now = time.monotonic()
        chat_id = message.chat.id if message.chat else 0
        if now - doc_hint_ts.get(chat_id, 0.0) < 60:
            return
        doc_hint_ts[chat_id] = now
        await message.answer(f"Need help? Try `/docs {topic}`", parse_mode=ParseMode.MARKDOWN)

    async def guard(message: Message, handler: Callable[[], Any]) -> None:
        start = time.monotonic()
        user_id = message.from_user.id if message.from_user else 0
        if not _is_allowed(user_id, config):
            await message.answer("Access denied.")
            return
        if not global_limiter.allow():
            metrics.error("global_rate_limit")
            await message.answer("System busy. Please retry shortly.")
            return
        if not rate_limiter.allow(user_id):
            metrics.error("rate_limit")
            await message.answer("Rate limited. Please slow down.")
            return
        metrics.inc("command")
        red_text = redact(message.text or "")
        logger.info("audit_command user_id=%s text=%s", user_id, red_text)
        try:
            await handler()
        except Exception:  # noqa: BLE001
            metrics.error("handler_error")
            logger.exception("Handler error")
            await message.answer("Unexpected error. Try again or see /docs troubleshooting.")
            await maybe_doc_hint(message, topic="troubleshooting")
            asyncio.create_task(
                alert_sink.notify(
                    "handler_error",
                    {"user_id": user_id, "text": red_text},
                )
            )
        finally:
            metrics.add_latency((time.monotonic() - start) * 1000)

    @dp.message(Command(commands=["start", "help"]))
    async def cmd_help(message: Message) -> None:
        async def run() -> None:
            text = (
                "Strix Telegram bot.\n"
                "/health\n"
                "/newrun <target> [instruction]\n"
                "/runs [query]\n"
                "/run <id> info|tail|report|files|docs\n"
                "/resume <id>\n"
                "/stop <id>\n"
                "/verbosity <id> <high-only|batched|full>\n"
                "/docs <topic>\n"
            )
            await message.answer(text)

        await guard(message, run)

    @dp.message(Command(commands=["health"]))
    async def cmd_health(message: Message) -> None:
        async def run() -> None:
            await message.answer("ok")

        await guard(message, run)

    @dp.message(Command(commands=["metrics"]))
    async def cmd_metrics(message: Message) -> None:
        async def run() -> None:
            lines = ["Counters:"]
            for k, v in metrics.counters.items():
                lines.append(f"{k}: {v}")
            lines.append("Errors:")
            for k, v in metrics.errors.items():
                lines.append(f"{k}: {v}")
            await message.answer("\n".join(lines))

        await guard(message, run)

    @dp.message(Command(commands=["newrun"]))
    async def cmd_newrun(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            args = command.args or ""
            parts = args.split(" ", 1)
            if not parts or not parts[0]:
                await message.answer("Usage: /newrun <target> [instruction]")
                return
            target = parts[0]
            instruction = parts[1] if len(parts) > 1 else None
            try:
                chat_id = message.chat.id
                run_id: Optional[str] = None

                async def flush_batch(rid: str) -> None:
                    await asyncio.sleep(BATCH_INTERVAL_SECONDS)
                    texts = run_batches.get(rid, [])
                    if not texts:
                        return
                    combined = "\n\n".join(texts)
                    if len(combined) > MAX_MESSAGE_CHARS:
                        combined = combined[:MAX_MESSAGE_CHARS] + "\n\n(truncated batch)"
                    await message.bot.send_message(chat_id=chat_id, text=combined, parse_mode=ParseMode.MARKDOWN)
                    run_batches[rid] = []
                    batch_tasks.pop(rid, None)

                def stream_callback(report_id: str, title: str, content: str, severity: str) -> None:
                    sev = severity.lower()
                    level = SEVERITY_LEVEL.get(sev, 0)
                    mode = run_verbosity.get(run_id or "", state.get_verbosity(run_id or "") or "high-only")
                    if mode == "high-only" and level < 3:
                        return
                    red_title = redact(title)
                    red_content = redact(content)
                    text = format_alert(sev, red_title, red_content[:1200])
                    if mode == "batched":
                        buf = run_batches.setdefault(run_id or "", [])
                        buf.append(text)
                        if run_id and run_id not in batch_tasks:
                            batch_tasks[run_id] = asyncio.create_task(flush_batch(run_id))
                    else:
                        asyncio.create_task(
                            message.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
                        )

                run_info = control_api.start_run(target=target, instruction=instruction, stream_callback=stream_callback)
                run_id = run_info.run_id
                logger.info("bot_run_started run_id=%s target=%s instruction=%s", run_id, target, (instruction or "").strip())
                default_mode = state.get_verbosity(run_id) or config.default_verbosity or "high-only"
                run_verbosity[run_id] = default_mode
                await message.answer(f"Started run {run_info.run_id} for target {run_info.target}")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to start run")
                await message.answer(f"Failed to start run: {exc}")
                await maybe_doc_hint(message)

        await guard(message, run)

    @dp.message(Command(commands=["runs"]))
    async def cmd_runs(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            query = (command.args or "").strip().lower()
            runs = control_api.list_runs()
            if query:
                runs = [r for r in runs if query in r.run_id.lower() or query in r.target.lower()]
            if not runs:
                await message.answer("No runs found.")
                return
            kb_rows = []
            for r in runs[:MAX_LIST_ITEMS]:
                kb_rows.append(
                    [
                        InlineKeyboardButton(
                            text=f"{r.run_id} ({r.status})",
                            callback_data=f"run_info:{r.run_id}",
                        )
                    ]
                )
            await message.answer("Select a run:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))

        await guard(message, run)

    @dp.message(Command(commands=["run"]))
    async def cmd_run(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            args = (command.args or "").split()
            if len(args) < 2:
                await message.answer("Usage: /run <id> <info|tail|report|files|docs>")
                await maybe_doc_hint(message)
                return
            run_id, subcmd = args[0], args[1]
            if subcmd == "info":
                info = control_api.get_run_info(run_id)
                if not info:
                    await message.answer("Run not found.")
                    await maybe_doc_hint(message)
                    return
                await message.answer(f"{info.run_id} - {info.target} - {info.status}")
            elif subcmd == "tail":
                logs, has_more, next_offset = fetch_tail_page(control_api, run_id, offset=0, page_size=50)
                kb_rows: list[list[InlineKeyboardButton]] = []
                if has_more:
                    kb_rows.append(
                        [
                            InlineKeyboardButton(
                                text="Tail more",
                                callback_data=f"tail_more:{run_id}:{next_offset}",
                            )
                        ]
                    )
                await message.answer("\n".join(logs) if logs else "No logs.", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None)
            elif subcmd == "report":
                summary = control_api.get_report_summary(run_id)
                if summary and len(summary) > MAX_MESSAGE_CHARS:
                    summary = summary[:MAX_MESSAGE_CHARS] + "\n\n(truncated)"
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Send full report",
                                callback_data=f"report_full:{run_id}",
                            )
                        ]
                    ]
                )
                await message.answer(summary or "No report yet.", reply_markup=kb)
            elif subcmd == "files":
                files = control_api.list_files(run_id)
                if not files:
                    await message.answer("No files.")
                    return
                kb_rows = build_file_kb(run_id, files, rel_path="")
                await message.answer("Select file or directory:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
            elif subcmd == "docs":
                await message.answer("Use /docs <topic> to fetch documentation excerpts.")
            else:
                await message.answer("Unknown subcommand.")

        await guard(message, run)

    @dp.message(Command(commands=["resume"]))
    async def cmd_resume(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            run_id = (command.args or "").strip()
            if not run_id:
                await message.answer("Usage: /resume <id>")
                await maybe_doc_hint(message)
                return
            chat_id = message.chat.id

            def stream_callback(report_id: str, title: str, content: str, severity: str) -> None:
                sev = severity.lower()
                level = SEVERITY_LEVEL.get(sev, 0)
                mode = run_verbosity.get(run_id, state.get_verbosity(run_id) or config.default_verbosity or "high-only")
                if mode == "high-only" and level < 3:
                    return
                text = format_alert(sev, redact(title), redact(content)[:1200])
                if mode == "batched":
                    buf = run_batches.setdefault(run_id, [])
                    buf.append(text)
                    if run_id not in batch_tasks:
                        batch_tasks[run_id] = asyncio.create_task(flush_batch_shared(run_id, chat_id))
                else:
                    asyncio.create_task(message.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN))

            async def flush_batch_shared(rid: str, cid: int) -> None:
                await asyncio.sleep(BATCH_INTERVAL_SECONDS)
                texts = run_batches.get(rid, [])
                if not texts:
                    return
                combined = "\n\n".join(texts)
                if len(combined) > MAX_MESSAGE_CHARS:
                    combined = combined[:MAX_MESSAGE_CHARS] + "\n\n(truncated batch)"
                await message.bot.send_message(chat_id=cid, text=combined, parse_mode=ParseMode.MARKDOWN)
                run_batches[rid] = []
                batch_tasks.pop(rid, None)

            try:
                ok = control_api.resume_run(run_id, stream_callback=stream_callback)
                if ok:
                    mode = state.get_verbosity(run_id) or config.default_verbosity or "high-only"
                    run_verbosity[run_id] = mode
                    await message.answer(f"Resumed streaming for {run_id} with verbosity {mode}.")
                else:
                    await message.answer(f"Run {run_id} not active; cannot resume. Consider starting a new run.")
                    await maybe_doc_hint(message)
            except NotImplementedError:
                await message.answer("Resume is not supported yet.")
                await maybe_doc_hint(message)

        await guard(message, run)

    @dp.message(Command(commands=["stop"]))
    async def cmd_stop(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            run_id = (command.args or "").strip()
            if not run_id:
                await message.answer("Usage: /stop <id>")
                await maybe_doc_hint(message)
                return
            try:
                if control_api.stop_run(run_id):
                    await message.answer(f"Stopped {run_id}")
                else:
                    await message.answer(f"Could not stop {run_id}")
                    await maybe_doc_hint(message)
            except NotImplementedError:
                await message.answer("Stop is not supported yet.")
                await maybe_doc_hint(message)

        await guard(message, run)

    @dp.message(Command(commands=["verbosity"]))
    async def cmd_verbosity(message: Message, command: CommandObject) -> None:
        async def run() -> None:
            args = (command.args or "").split()
            if len(args) != 2:
                await message.answer("Usage: /verbosity <id> <high-only|batched|full>")
                return
            run_id, mode = args
            if mode not in {"high-only", "batched", "full"}:
                await message.answer("Mode must be one of: high-only, batched, full.")
                return
            run_verbosity[run_id] = mode
            state.set_verbosity(run_id, mode)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="High-only", callback_data=f"verbosity:{run_id}:high-only"),
                        InlineKeyboardButton(text="Batched", callback_data=f"verbosity:{run_id}:batched"),
                        InlineKeyboardButton(text="Full", callback_data=f"verbosity:{run_id}:full"),
                    ]
                ]
            )
            await message.answer(f"Verbosity for {run_id} set to {mode}.", reply_markup=kb)

        await guard(message, run)

    @dp.message(F.text)
    async def fallback(message: Message) -> None:
        await message.answer("Unrecognized command. Send /help.")

    @dp.callback_query(F.data.startswith("report_full:"))
    async def report_full(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 1)
        if len(parts) != 2:
            await cb.answer()
            return
        run_id = parts[1]
        try:
            file_path = control_api.get_report_file(run_id)
            if not file_path:
                await cb.message.answer("Report file not found.")
                await cb.answer()
                return
            size = os.path.getsize(file_path)
            if size > MAX_FILE_SIZE_BYTES:
                await cb.message.answer("Report too large to send. Please retrieve manually.")
                await cb.answer()
                return
            with open(file_path, "rb") as fh:
                logger.info("bot_report_send run_id=%s path=%s size=%s", run_id, file_path, size)
                await cb.message.answer_document(document=fh)
        except TelegramBadRequest as exc:
            await cb.message.answer(f"Failed to send report: {exc}")
            asyncio.create_task(
                alert_sink.notify(
                    "delivery_error",
                    {"run_id": run_id, "path": file_path, "error": str(exc)},
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to send report")
            await cb.message.answer(f"Failed to send report: {exc}")
            asyncio.create_task(alert_sink.notify("delivery_error", {"run_id": run_id, "path": file_path, "error": str(exc)}))
        await cb.answer()

    @dp.callback_query(F.data.startswith("run_info:"))
    async def run_info_cb(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 1)
        if len(parts) != 2:
            await cb.answer()
            return
        run_id = parts[1]
        info = control_api.get_run_info(run_id)
        if not info:
            await cb.message.answer("Run not found.")
            await cb.answer()
            return
        text = f"{info.run_id}\nTarget: {info.target}\nStatus: {info.status}"
        await cb.message.answer(text)
        await cb.answer()

    @dp.callback_query(F.data.startswith("tail_more:"))
    async def tail_more(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 2)
        if len(parts) != 3:
            await cb.answer()
            return
        run_id, offset_str = parts[1], parts[2]
        try:
            offset = int(offset_str)
        except ValueError:
            await cb.answer()
            return
        logs, has_more, next_offset = fetch_tail_page(control_api, run_id, offset=offset, page_size=50)
        kb_rows: list[list[InlineKeyboardButton]] = []
        if has_more:
            kb_rows.append(
                [
                    InlineKeyboardButton(
                        text="Tail more",
                        callback_data=f"tail_more:{run_id}:{next_offset}",
                    )
                ]
            )
        await cb.message.answer(
            "\n".join(logs) if logs else "No logs.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None,
        )
        await cb.answer()

    @dp.callback_query(F.data.startswith("file_nav:"))
    async def file_nav(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 2)
        if len(parts) != 3:
            await cb.answer()
            return
        run_id, rel_path = parts[1], parts[2]
        try:
            files = control_api.list_files(run_id, rel_path)
            if not files:
                await cb.message.answer("No files.")
                await cb.answer()
                return
            kb_rows = build_file_kb(run_id, files, rel_path=rel_path)
            await cb.message.answer(f"Browsing `{rel_path or '.'}`", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to browse files")
            await cb.message.answer(f"Failed to browse files: {exc}")
        await cb.answer()

    @dp.callback_query(F.data.startswith("file_dl:"))
    async def file_dl(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 2)
        if len(parts) != 3:
            await cb.answer()
            return
        run_id, rel_path = parts[1], parts[2]
        try:
            meta = control_api.get_file_metadata(run_id, rel_path)
            if not meta:
                await cb.message.answer("File not found.")
                await cb.answer()
                return
            file_path, size = meta
            if size > MAX_FILE_SIZE_BYTES:
                await cb.message.answer("File too large to send. Please fetch manually.")
                await cb.answer()
                return
            with open(file_path, "rb") as fh:
                logger.info("bot_file_send run_id=%s path=%s size=%s", run_id, rel_path, size)
                await cb.message.answer_document(document=fh)
        except TelegramBadRequest as exc:
            await cb.message.answer(f"Failed to send file: {exc}")
            asyncio.create_task(
                alert_sink.notify(
                    "delivery_error",
                    {"run_id": run_id, "path": rel_path, "error": str(exc)},
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to send file")
            await cb.message.answer(f"Failed to send file: {exc}")
            asyncio.create_task(alert_sink.notify("delivery_error", {"run_id": run_id, "path": rel_path, "error": str(exc)}))
        await cb.answer()

    @dp.callback_query(F.data.startswith("verbosity:"))
    async def verbosity_cb(cb: CallbackQuery) -> None:
        data = cb.data or ""
        parts = data.split(":", 2)
        if len(parts) != 3:
            await cb.answer()
            return
        run_id, mode = parts[1], parts[2]
        if mode not in {"high-only", "batched", "full"}:
            await cb.answer()
            return
        run_verbosity[run_id] = mode
        state.set_verbosity(run_id, mode)
        await cb.message.answer(f"Verbosity for {run_id} set to {mode}.")
        await cb.answer()

    return dp


def build_http_app(metrics: Metrics, token: str | None = None) -> web.Application:
    app = web.Application()

    async def _auth(request: web.Request) -> bool:
        if not token:
            return True
        provided = request.headers.get("Authorization", "")
        return provided == f"Bearer {token}"

    async def health_handler(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def metrics_handler(request: web.Request) -> web.Response:
        if not await _auth(request):
            return web.Response(status=403)
        fmt = request.query.get("format", "json")
        counters = metrics.counters
        errors = metrics.errors
        latencies = metrics.latencies_ms
        if fmt == "prom":
            lines = []
            for k, v in counters.items():
                lines.append(f"strix_bot_counter{{name=\"{k}\"}} {v}")
            for k, v in errors.items():
                lines.append(f"strix_bot_error_total{{name=\"{k}\"}} {v}")
            if latencies:
                avg = sum(latencies) / len(latencies)
                lines.append(f"strix_bot_command_latency_ms_avg {avg:.2f}")
            return web.Response(text="\n".join(lines), content_type="text/plain")
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        return web.json_response({"counters": counters, "errors": errors, "avg_latency_ms": avg_latency})

    app.add_routes(
        [
            web.get("/healthz", health_handler),
            web.get("/health", health_handler),
            web.get("/metrics", metrics_handler),
        ]
    )
    return app


async def run_bot(control_api: ControlAPI, config: TelegramBotConfig) -> None:
    bot = Bot(token=config.bot_token)
    dp = create_dispatcher(control_api, config)
    runner: web.AppRunner | None = None
    if config.http_port:
        app = build_http_app(dp.metrics, token=config.http_token)  # type: ignore[arg-type, attr-defined]
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=config.http_host or "0.0.0.0", port=config.http_port)
        await site.start()
        logger.info("HTTP server started on %s:%s", config.http_host or "0.0.0.0", config.http_port)

    if not config.webhook_url:
        raise RuntimeError("Webhook URL not configured.")
    await bot.set_webhook(config.webhook_url)
    await dp.start_polling(bot)
    if runner:
        await runner.cleanup()


def run(control_api: ControlAPI, config: TelegramBotConfig) -> None:
    asyncio.run(run_bot(control_api, config))
