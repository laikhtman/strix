# Telegram Bot E2E Staging Plan

Purpose: validate the Telegram bot end-to-end in a staging chat before wider rollout.

## Preconditions
- Staging Telegram chat exists; operators are allowlisted (`ALLOWLIST_IDS`).
- Bot deployed to staging VM with webhook HTTPS reachable; `BOT_TOKEN`, `WEBHOOK_URL`, `STRIX_ROOT` set.
- Sample target app available for scans (non-production, safe to probe).
- Optional: `BOT_HTTP_PORT` exposed to staging network for `/health`/`/metrics`.

## Test steps
1) Sanity: send `/health` and `/start`; expect `ok` and help text.
2) Start run: `/newrun <staging-target> --instruction "smoke"`; expect acknowledgment with run id.
3) Streaming: during run, confirm vulnerability messages arrive with severity icons; switch verbosity `/verbosity <id> batched` then `full` and observe differences.
4) Tail logs: `/run <id> tail` then press “Tail more” until end; ensure pagination stops.
5) Report: `/run <id> report` -> receive summary; press “Send full report” -> receive file.
6) Files: `/run <id> files` -> navigate directories; download a small file; confirm size guard blocks oversized file if present.
7) Docs: `/run <id> docs` or `/docs troubleshooting` -> receive excerpt/link.
8) Search runs: `/runs <partial>` -> list filtered runs; open run info via buttons.
9) Stop: `/stop <id>` on a live run -> confirm stop message.
10) Metrics/health: curl `/health` and `/metrics?format=prom` (with token if set); ensure non-200 failures are alerted/logged.

## Pass criteria
- All commands respond within a few seconds; no unhandled errors in bot logs.
- Streaming respects verbosity and redaction; batching does not exceed Telegram limits.
- File/report sends succeed or are gracefully blocked with messaging.
- `/metrics` exposes counters/errors; `/health` returns `ok`.

## Post-test
- Capture transcripts/screenshots.
- File any bugs with run id, timestamps, and screenshots.
- Clear staging secrets if rotated for the test.
