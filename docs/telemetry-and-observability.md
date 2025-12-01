# Telemetry and Observability

## Tracer
- Location: `telemetry/tracer.py`.
- Responsibilities: track agent creation/status changes, tool execution start/finish, vulnerability findings, scan config metadata.
- Global tracer set via `set_global_tracer`; CLI sets vulnerability callback to render panels.

## Events
- Agent lifecycle: creation, status updates (running/waiting/finished).
- Tool executions: start/end, args, results, status.
- Vulnerabilities: id/title/content/severity routed to UI.

## Extending telemetry
- Add new methods or fields in `tracer.py`; ensure thread safety where needed.
- Update UI renderers if new event types should be displayed.
- Redact sensitive data before logging or emitting.

## Consumption
- TUI/CLI read tracer callbacks for live updates.
- Persist outputs in `strix_runs/<run_name>` (extend to send elsewhere if needed).
- Structured exports: `vulnerabilities.csv`, `vulnerabilities.jsonl`, and SARIF `vulnerabilities.sarif.json` for CI-friendly ingestion.

## Maintenance
- Update event fields when tracer schema evolves; ensure UI renderers are aligned with new telemetry.
