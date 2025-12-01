# Telegram Bot Usage (Planned)

## Prerequisites
- Bot token stored in env/secret manager.
- Webhook HTTPS endpoint reachable; webhook set to bot URL.
- Allowlisted Telegram user IDs configured.
- Bot service running (systemd) with access to `strix_runs/`.
- Start: `poetry run strix-bot --mode strix` (default) or `--mode fs` for read-only browsing.
- Env validation: BOT_TOKEN (or BOT_TOKEN_FILE), WEBHOOK_URL, and ALLOWLIST_IDS must be set or the bot will refuse to start.
- Optional HTTP endpoints (if BOT_HTTP_PORT set): `/health`, `/healthz`, `/metrics`.
- Protect optional HTTP endpoints with `BOT_HTTP_TOKEN` (Bearer token for `/metrics`).
- Optional tuning: `BOT_RATE_LIMIT` (per-user seconds, default 1.0), `BOT_GLOBAL_RATE_LIMIT` (seconds, default 0.5), `BOT_DEFAULT_VERBOSITY` (`high-only|batched|full`, default `high-only`).
- `.env` supported in repo root; see `.env.example`.

## Commands
- `/start` - greet and show help.
- `/help` - list commands and usage hints.
- `/health` - simple health check (responds with "ok").
- `/metrics` - show in-memory counters/errors.
- `/newrun <target> [instruction]` - start a scan with optional instruction.
- `/runs [query]` - list recent runs (filter by run_id/target substring).
- `/run <id> info` - show run metadata/status.
- `/run <id> tail` - tail recent logs (paginated).
- `/run <id> report` - send summary; button to request full report file.
- `/run <id> files` - browse `strix_runs/<id>` via buttons; download files (size limits apply).
- `/run <id> docs` - show links/excerpts to relevant docs.
- `/resume <id>` - reattach streaming to an active run if possible; otherwise reply with guidance.
- `/stop <id>` - stop a run.
- `/verbosity <id> <mode>` - set per-run verbosity: `high-only | batched | full`.
- `/docs <topic>` - fetch doc excerpt + link.

Current status:
- Command handlers wired; start/stop/status/logs/files/reports draft-wired via StrixControlAPI.
- Resume reattaches streaming only if the run is still active; otherwise guidance is shown.
- Inline keyboards for reports and file nav/download with parent navigation; size guards enforced.
- `/docs <topic>` returns excerpt from local docs directory.
- `/verbosity` stores preference for future streaming (no effect yet).
- Long report summaries are truncated to fit Telegram message limits; full report available via button.
- Streaming: vulnerability findings are pushed to chat when runs start; high-only mode filters out lower severities; batched mode groups messages every few seconds (no persistence); messages include severity icons and per-message truncation.

## Interactions
- Inline keyboards for: open report summary/full, tail next page, change verbosity, navigate files.
- Tailing stops showing the "Tail more" button once the end of the log is reached.
- Verbosity defaults to summaries/high-severity; user can elevate per run.
- Redaction on by default; explicit confirmation required to send sensitive content.
- Default verbosity can be set via `BOT_DEFAULT_VERBOSITY` to align with operator preference.

## Examples
- Start: `/newrun https://example.com --instruction "Focus on auth flows"`
- List runs: `/runs`
- Set verbosity: `/verbosity run-123 batched`
- Fetch report summary: button from `/run run-123 report`

## Safety
- Allowlist enforced on every command.
- Path sanitization on file browsing.
- Size checks/compression before sending files.
- Rate limits on outbound messages to avoid flooding (basic per-user limiter in place).
- Command logging/metrics counters enabled (internal only; errors counted for rate limits).
- Structured logs emitted for commands, run starts, reports, and file sends.
- Alerts: optional `BOT_ALERT_WEBHOOK` receives JSON on delivery/handler errors.
- If HTTP endpoints are enabled, restrict exposure (firewall/allowlist) and avoid exposing them publicly.
- HTTP `/metrics` supports `?format=prom` for Prometheus-style plaintext.
- Tests: missing env vars are covered by `tests/test_bot_config.py`; run `poetry run pytest`.
- Tests: rate limiter/metrics helpers covered by `tests/test_bot_misc.py`.
- Tests: streaming severity/batch filters covered by `tests/test_bot_streaming.py`.
- Tests: HTTP endpoints (`/healthz`, `/metrics`) covered by `tests/test_bot_http.py`.
- Tests: metrics latency tracking covered by `tests/test_bot_metrics.py`.
- CI: see `docs/setup-and-running.md` for GitHub Actions example to run pytest.
- BOT_TOKEN_FILE is supported for secret injection; ensure file is protected and readable.
- Streaming redacts obvious secrets (e.g., tokens prefixed with `sk-`) before sending.
- Verbosity preferences are persisted in SQLite (`BOT_DB_PATH`).
- On certain errors, the bot will suggest `/docs troubleshooting` (throttled to avoid spam).
- `/metrics` requires `Authorization: Bearer <BOT_HTTP_TOKEN>` when token is set.
- Tests: control API listing fallback covered by `tests/test_control_api_list.py`.
- Secret management: use env vars or mount a secret to `BOT_TOKEN_FILE`; systemd drop-ins can set `EnvironmentFile`.

## Deployment (VM/systemd)
- Set env: `BOT_TOKEN`, `WEBHOOK_URL`, `ALLOWLIST_IDS`, `STRIX_ROOT` (if needed).
- Use `packaging/systemd/strix-bot.service` as a template (copy to `/etc/systemd/system/` and adjust paths/user/env).
- Run systemd service; confirm health checks (`/health`, `/healthz`) respond.
- Verify webhook set via bot API; test `/start` from allowlisted user.

## Troubleshooting (high level)
- No responses: check systemd status/logs; verify webhook URL/token.
- Missing files: confirm `strix_runs/` path and permissions.
- Rate limit errors: adjust batching/severity filters.
