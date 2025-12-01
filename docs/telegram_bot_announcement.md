# Telegram Bot Announcement (Internal)

Audience: engineering/operators. Goal: share availability, how to use, and safety notes.

## Key points
- What: Strix Telegram bot to start/stop runs, stream findings, fetch reports/files, and browse docs.
- Where: staging/prod bot at your usual Telegram; access controlled by allowlist (`ALLOWLIST_IDS`).
- Status: pilot complete; ready for wider use. Resume remains unsupported (will reply with guidance).

## How to start
1) Ensure you are allowlisted; ask the ops team if not.
2) Use `/start` for help, `/health` to confirm it’s alive.
3) Launch a run: `/newrun https://target --instruction "focus on auth"`.
4) During the run: adjust verbosity `/verbosity <id> batched|full`, tail logs `/run <id> tail`, view summary `/run <id> report`, and fetch files `/run <id> files`.
5) Get docs: `/docs troubleshooting` or `/run <id> docs`.

## Safety
- Allowlist enforced; tokens via env/secret manager (`BOT_TOKEN`/`BOT_TOKEN_FILE`).
- Redaction on streaming; reports/files are sent as-is—avoid sensitive targets unless approved.
- Size/path guards on file browsing; rate limits configurable via env.
- Optional HTTP `/health`/`/metrics` secured by host/IP + `BOT_HTTP_TOKEN` if set.

## Support
- Issues: check `/health`, service logs, and `/metrics?format=prom` (with token if configured).
- Alerts: delivery/handler failures are emitted to `BOT_ALERT_WEBHOOK` when configured.
- Docs: `docs/telegram_bot_usage.md`, `docs/telegram_bot_troubleshooting.md` (or `/docs troubleshooting`).
