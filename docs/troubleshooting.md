# Troubleshooting

## Common issues and fixes
- Docker daemon not running: start service; confirm `docker ps` works.
- Cannot pull/run images: check permissions/registry auth; pre-pull image.
- Playwright missing: run `python -m playwright install --with-deps`.
- Invalid/missing LLM key: set `STRIX_LLM` and `LLM_API_KEY`; verify base URL for proxy.
- LLM timeouts/slow responses: increase provider timeout in config; check network; reduce parallelism.
- Port conflicts for proxy/browser tools: free the port or configure alternate.
- Missing outputs: ensure `strix_runs/<run_name>` writable; check tracer logs.
- Telegram bot webhook not responding: verify `WEBHOOK_URL`, TLS, and bot token; check service logs.
- Telegram bot rate-limited: slow down commands; adjust limiter if necessary.
- Telegram report send fails: ensure report file exists, size under Telegram limit, and bot has FS access.
- Telegram resume fails: resume is not supported with current agent state; restart a new run instead.
- Streaming messages not arriving: ensure run started via bot so tracer callback is set; check chat allowlist and bot logs.
- Streaming misses low severity findings: expected when verbosity is high-only; set `/verbosity <id> full` to receive all, or `batched` to group them.
- Bot fails to start: ensure `BOT_TOKEN`, `WEBHOOK_URL`, and `ALLOWLIST_IDS` are set.
- HTTP `/health` or `/healthz` unreachable: check `BOT_HTTP_PORT`/`BOT_HTTP_HOST` values and systemd service logs.
- HTTP `/metrics` unreachable: set `BOT_HTTP_PORT`/`BOT_HTTP_HOST` or use `/metrics` command in chat.
- Using `BOT_TOKEN_FILE`: ensure the file is readable, contains only the token, and path is correct.
- Sensitive content showing in streamed messages: redaction masks some token prefixes; avoid instructing bot to send secrets or use full report manually with care.
- HTTP `/metrics` returns 403: set `BOT_HTTP_TOKEN` and include `Authorization: Bearer <token>`.
- Delivery alerts: if using `BOT_ALERT_WEBHOOK`, verify the endpoint is reachable and inspect received payloads for failures.
- Resume fails: the bot can only reattach streaming to runs that are still active; if the run is finished or not found, start a new run.

## Logs and locations
- Run artifacts under `strix_runs/<run_name>`.
- Use tracer output (CLI/TUI) for tool/vulnerability events.
- Check docker container logs for runtime/tool_server failures.
- Bot service logs (systemd) for webhook/command handling issues.

## Escalation decision tree
1) Identify failing component (LLM, docker, tool server, UI).  
2) Re-run with `-n` to simplify UI surface.  
3) Enable verbose logging (add temporary prints/logging in failing module).  
4) If external provider issue persists, switch to alternate model/provider.  
5) Capture minimal repro and add to regression tests.  

## Maintenance
- Add new failure modes as they surface; keep log locations updated if paths change.
