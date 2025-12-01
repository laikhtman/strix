# Interface (CLI/TUI)

## Entrypoints
- `interface/main.py`: CLI entry, argument parser wiring, dispatch to CLI/TUI.
- `interface/cli.py`: non-interactive flow; renders startup panel and vulnerability panels via tracer callbacks.
- `interface/tui.py`: textual-based interactive UI; panels for tools, logs, stats.
- `interface/utils.py`: stats builders, severity colors, shared helpers.

## Arguments (key)
- `--target/-t`: target path/URL (multi allowed).
- `--instruction`: freeform guidance to agent.
- `--non-interactive/-n`: headless mode; prints findings to stdout.
- `--run-name`: optional custom run id (otherwise generated).
- Provider/env vars read separately; ensure `STRIX_LLM`/`LLM_API_KEY` set.

## Rendering
- Tool outputs mapped via `interface/tool_components/*` renderers (browser, proxy, terminal, file edits, reports, notes, thinking, etc.).
- Live stats and final stats built in `utils.py` and displayed in panels.
- Vulnerabilities emitted from tracer callback in CLI mode; TUI shows panes with updates.

## Customization
- Styles in `interface/assets/tui_styles.tcss`.
- Add new renderers by extending `tool_components/base_renderer.py` and registering in `registry.py`.

## Non-interactive behavior
- Skips TUI; logs findings immediately.
- Still writes outputs under `strix_runs/<run_name>`.

## Maintenance
- Update argument list when CLI flags change; refresh renderer mapping when new tools are added.
