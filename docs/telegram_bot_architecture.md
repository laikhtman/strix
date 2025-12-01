# Telegram Bot Architecture (aiogram + webhook, sidecar VM)

## Overview
- Transport: Webhook (HTTPS endpoint) to receive Telegram updates.
- Bot runtime: aiogram app running as a systemd-managed service on the same VM as Strix (sidecar).
- Control surface: internal Python API layer that starts/stops/resumes/lists runs without spawning CLI subprocesses.
- Auth: allowlisted Telegram user IDs gate all commands; secrets via env/secret manager.
- Persistence: SQLite for bot session state (pagination, recent runs).
- Filesystem access: direct read access to `strix_runs/` for reports/artifacts.

## Data/Control Flow
```
Telegram -> Webhook endpoint (aiogram) -> Command/handler
    -> Auth check (allowlist)
    -> Control API (start/stop/resume/list/tail) -> Strix internals
    -> Tracer hooks stream vulns/logs -> Bot push to Telegram
    -> FS access to strix_runs -> send summaries/files/docs
```

## Key Components
- Webhook handler: receives updates, routes to aiogram routers.
- Command handlers: `/newrun`, `/runs`, `/run <id> info/tail/report/files/docs`, `/resume`, `/stop`, `/verbosity`, `/docs`, `/help`.
- Inline keyboards: quick actions for reports/files/tail/verbosity.
- Control API: Python functions wrapping Strix interfaces (no CLI spawn) to manage runs and fetch status.
- Telemetry bridge: tracer callbacks batch/format vulnerability events and push to Telegram respecting verbosity (high-only/batched/full) with severity icons.
- File serving: safe path resolver for `strix_runs/<run_name>` artifacts; enforce size limits and compression.
- Docs serving: excerpts/links from `docs/*.md`, optional contextual suggestions after errors.
- Rate limiting: global/severity-based throttling of outbound messages.
- Security: allowlist check per request; redaction by default; explicit override for sensitive data.
- Alerting: optional webhook receives JSON payloads when delivery/handler errors occur.
- Tunables: per-user/global rate limits and default verbosity via env (`BOT_RATE_LIMIT`, `BOT_GLOBAL_RATE_LIMIT`, `BOT_DEFAULT_VERBOSITY`).
- Config loading: `.env` in repo root supported; env vars override file values.

## Deployment
- Systemd unit running aiogram app with webhook URL + token via env.
- Health check endpoint (HTTP/ping) for monitoring.
- Optional HTTP server (if BOT_HTTP_PORT set) exposing `/health`, `/healthz`, and `/metrics` (in-memory counters/errors).
- TLS termination via reverse proxy or direct cert; ensure webhook set to HTTPS URL.

## Observability
- Structured logs for commands, control API calls, run starts, report sends, and file transfers.
- Metrics (commands, errors, latency, message volume); `/metrics` supports JSON or Prom text format and can be scraped by Prometheus.
- Alerting on delivery/API failures once metrics exist.

## Maintenance Notes
- Update allowlist when adding operators.
- Rotate bot token regularly; store in secret manager/env.
- Re-run webhook set-up if URL/cert changes.
