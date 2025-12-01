# Setup and Running

## Prerequisites
- Python 3.12
- Docker running with permissions to pull/run images.
- Playwright browsers installed (one-time): `python -m playwright install --with-deps`.
- Network access to chosen LLM provider or litellm proxy.

## Install
```bash
# Recommended
pipx install strix-agent

# From source
poetry install
poetry run strix --help
```

## Environment variables
- `STRIX_LLM`: provider/model id (e.g., `openai/gpt-5`).
- `LLM_API_KEY`: API key for the provider or proxy.
- Optional provider settings: set according to `llm/config.py` expectations (e.g., base URL for litellm proxy).

## Running scans
- Basic local scan: `strix --target ./app-directory`
- Remote repo: `strix --target https://github.com/org/repo`
- Web app: `strix --target https://your-app.com`
- Multiple targets: `strix -t <target1> -t <target2>`
- Add instructions: `--instruction "Focus on IDOR"`
- Non-interactive mode (for servers/CI): `strix -n --target https://your-app.com`

## Outputs
- Results saved under `strix_runs/<run_name>`; includes reports/logs.
- Structured vulnerability exports in each run: `vulnerabilities/*.md`, `vulnerabilities.csv`, `vulnerabilities.jsonl`, and `vulnerabilities.sarif.json` for CI upload.
- Non-interactive mode also streams findings to stdout.

## Common pitfalls
- Docker not running → ensure daemon is up and user has permissions.
- Playwright missing → rerun `python -m playwright install --with-deps`.
- Invalid/missing `LLM_API_KEY` → verify env; check provider-specific base URL if using proxy.
- Slow runs → confirm network connectivity and increase provider timeout if needed in config.

## Telegram bot (sidecar, planned)
- Env: `BOT_TOKEN`, `WEBHOOK_URL`, `ALLOWLIST_IDS`, optional `BOT_DB_PATH`, `STRIX_ROOT`.
- Deploy bot service on same VM with access to `strix_runs/`; ensure webhook HTTPS endpoint reachable.
- Commands and usage: see `docs/telegram_bot_usage.md`.
- Architecture and security notes: see `docs/telegram_bot_architecture.md`.
- Start bot: `poetry run strix-bot --mode strix` (or `--mode fs` for read-only browsing).
- Supports `.env` in repo root; see `.env.example` for all keys (env vars still take priority).
- Systemd unit template: `packaging/systemd/strix-bot.service` (copy to `/etc/systemd/system/` and adjust paths/user/env).
- Health endpoints (if `BOT_HTTP_PORT` set): `/health` and `/healthz` return `ok`; `/metrics` returns JSON or Prometheus when `?format=prom`.
- Optional tuning: `BOT_RATE_LIMIT` (per-user seconds), `BOT_GLOBAL_RATE_LIMIT` (seconds), `BOT_DEFAULT_VERBOSITY` (high-only|batched|full).
- Sample systemd (adjust paths/env):
  ```
  [Unit]
  Description=Strix Telegram Bot
  After=network.target

  [Service]
  WorkingDirectory=/opt/strix
  Environment=BOT_TOKEN=...
  Environment=WEBHOOK_URL=https://your-domain/bot-webhook
  Environment=ALLOWLIST_IDS=12345,67890
  Environment=BOT_HTTP_PORT=8081
  Environment=BOT_HTTP_HOST=0.0.0.0
  ExecStart=/usr/bin/poetry run strix-bot --mode strix
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```
- Security: prefer injecting `BOT_TOKEN` via secret manager or systemd drop-in rather than files; rotate tokens regularly (mount secret to `BOT_TOKEN_FILE` if using file-based secret).
- Secure HTTP endpoints (`/health`, `/healthz`, `/metrics`) with firewall/allowlist if enabled.
- Use `BOT_HTTP_TOKEN` to require bearer auth on `/metrics`; rotate regularly.
- CI: add a job to run `poetry run pytest` to cover config, streaming filters, HTTP endpoints.
- A ready-made workflow exists at `.github/workflows/bot-tests.yml` to run bot tests in CI.
- Alerts: set `BOT_ALERT_WEBHOOK` to receive JSON alerts on bot handler/delivery failures.
- `.env` also supports core LLM settings (`STRIX_LLM`, `LLM_API_KEY`, optional `LLM_API_BASE`).
- Example GitHub Actions job:
  ```yaml
  bot-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install poetry
          poetry install --with dev
      - name: Test
        run: poetry run pytest tests
  ```
- Secret management example (systemd drop-in):
  ```
  # /etc/systemd/system/strix-bot.service.d/10-secret.conf
  [Service]
  EnvironmentFile=/etc/strix-bot/secret.env  # contains BOT_TOKEN=...
  ```

## Maintenance
- Update commands when CLI flags change; refresh provider env guidance when new providers added.
