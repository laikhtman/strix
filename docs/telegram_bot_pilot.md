# Telegram Bot Pilot & Rollout

Plan for piloting with allowlisted users, collecting feedback, and rolling out.

## Pilot setup
- Scope: staging or low-risk production targets; keep allowlist small (operators only).
- Config: `BOT_TOKEN`, `WEBHOOK_URL`, `ALLOWLIST_IDS`, optional `BOT_ALERT_WEBHOOK` for failures.
- Ensure `/health` and `/metrics` reachable to operators (behind firewall/auth as needed).
- Share usage doc: `docs/telegram_bot_usage.md`; remind users about redaction/limits.

## Pilot checklist (1–2 weeks)
- Create at least 3 runs across different targets.
- Validate streaming at all verbosity levels.
- Fetch reports/files and exercise size guards.
- Use `/docs troubleshooting` after an induced error to verify hints.
- Capture any delivery/API errors (check alerts and bot logs).
- Track UX notes: confusing messages, missing buttons, verbosity defaults.

## Feedback and hardening
- Review pilot feedback; categorize into bugs vs. UX tweaks.
- Adjust rate limits, default verbosity, or button labels based on feedback.
- Add missing docs/tests from pilot findings.

## Rollout
- Expand allowlist; announce availability in internal channels with brief “how to”.
- Ensure CI workflow (`.github/workflows/bot-tests.yml`) is green.
- Monitor `/metrics` errors and alert webhook for the first week; be ready to toggle bot off via systemd.
- Update README/marketing if broader audience is desired.

## Exit criteria
- No critical delivery/API errors in pilot week.
- Users can start runs, receive streaming updates, fetch reports/files, and browse docs without intervention.
- Health/metrics endpoints monitored; alert webhook functioning if configured.
