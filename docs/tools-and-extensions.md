# Tools and Extensions

## Tool contract
- Each tool has an XML action schema (`*_actions_schema.xml`) describing available actions and arguments.
- Python implementations live alongside schemas (e.g., `tools/browser/browser_actions.py`).
- `tools/registry.py` registers tool classes; `tools/executor.py` executes invocations.
- Tool outputs feed into UI renderers (`interface/tool_components/*`) for visualization.

## Tool catalog (purpose)
- `agents_graph`: manage/render agent graph data.
- `browser`: Playwright-driven browsing, tabs, interactions.
- `file_edit`: apply edits to files.
- `finish`: signal task completion.
- `notes`: capture structured notes.
- `proxy`: HTTP proxy controls.
- `python`: execute sandboxed Python.
- `reporting`: reporting actions (vuln reports with severity + optional CVSS/CWE/references/fix hints).
- `sast`: lightweight static and dependency scanning (Python patterns + unpinned deps).
- `api_probe`: load OpenAPI specs and suggest fuzz payloads for endpoints.
- `terminal`: terminal session actions.
- `thinking`: internal deliberation steps.
- `web_search`: web search actions.

## Adding a tool
1) Create folder under `tools/<name>/`.
2) Write schema XML defining actions and args.
3) Implement actions in `<name>_actions.py`; ensure safe defaults/timeouts.
4) Register in `tools/registry.py`.
5) Add renderer in `interface/tool_components/` if UI output needed.
6) Add tests (unit + integration) covering schema parsing and execution.
7) Document in this file and update CLI help if flags added.

## Safeguards
- Respect execution limits/timeouts in implementations.
- Validate inputs from LLM; sanitize file paths and network targets where applicable.
- Log via tracer for observability.

## Renderers
- Base renderer in `interface/tool_components/base_renderer.py`.
- Specialized renderers map tool outputs to TUI panels (browser, proxy, terminal, reporting, etc.).
- Register renderers in `interface/tool_components/registry.py`.

## Maintenance
- Update catalog when adding/removing tools; keep schemas and registry references in sync; refresh safety notes when execution constraints change.
