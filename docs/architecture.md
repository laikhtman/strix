# Architecture

Strix runs coordinated agents that drive tools inside a dockerized sandbox, orchestrated via CLI/TUI, with telemetry and prompt packs guiding behavior.

## System map
- Entry: CLI/TUI (`interface/main.py`, `cli.py`, `tui.py`) parses args, sets scan config, starts tracer callbacks.
- Agent loop: `agents/base_agent.py`, `agents/state.py`, `agents/StrixAgent/strix_agent.py` manage iterations, messages, tool calls, memory compression.
- Tools: `tools/*` define XML action schemas + Python implementations; `tools/registry.py` registers; `tools/executor.py` dispatches; `interface/tool_components/*` render outputs.
- Runtime: `runtime/docker_runtime.py`, `runtime/tool_server.py`, `runtime/runtime.py` manage sandbox containers and tool execution endpoints.
- LLM: `llm/llm.py`, `llm/config.py`, `llm/request_queue.py`, `llm/memory_compressor.py` handle provider routing, retries, queueing, token budgeting.
- Prompts: `prompts/**/*.jinja`, `agents/StrixAgent/system_prompt.jinja`, `prompts/coordination/root_agent.jinja` supply structured instructions.
- Telemetry: `telemetry/tracer.py` captures agent lifecycle, tool executions, vulnerabilities; `interface/utils.py` renders stats.
- Outputs: run artifacts under `strix_runs/<run_name>` (reports/logs).

## Data flow (simplified)
1) User invokes `strix` -> `interface/main.py` builds args, `cli.py`/`tui.py` start UI.  
2) Scan config + tracer created -> `StrixAgent` instantiated with `LLMConfig`.  
3) Agent loop requests LLM completions; responses trigger tool invocations via `tools/executor.py`.  
4) Tools call `runtime/tool_server.py` (docker sandbox) for side effects (browser, proxy, terminal, python, file edits, etc.).  
5) Tool results and tracer events propagate to UI renderers; vulnerabilities emitted to console and saved.  
6) Loop continues until max iterations, finish action, or user stop; results stored in `strix_runs/`.

## ASCII data flow
```
CLI/TUI -> Tracer -> StrixAgent -> LLM -> Tool Executor -> Runtime (Docker) -> Tool Server
             ^                                           |
             |-------------------------------------------+
```

## Extension seams
- Add tools: new folder under `tools/`, schema XML, implementation, registry entry, renderer in `interface/tool_components/`.
- Add prompts: new Jinja in `prompts/*` or agent prompt folder; wire selection logic where consumed.
- Add telemetry: emit via `telemetry/tracer.py` helper methods; extend UI renderers to display.
- Add providers: extend `llm/config.py` + `llm/llm.py` to create client, auth, and request path.
- Adjust runtime: modify `runtime/docker_runtime.py` for images/limits, `tool_server.py` for endpoints.

## Persistence
- Runs: `strix_runs/<run_name>` contains reports and logs (non-interactive mode prints to stdout too).
- Agent graph: managed in-memory via `tools/agents_graph/agents_graph_actions.py`, rendered by interface.

## Non-interactive mode
- Enabled via `-n/--non-interactive`; suppresses interactive UI, streams findings to stdout; still uses tracer callbacks for vulnerability events.

## Reliability and limits
- Max iterations default 300 (`BaseAgent.max_iterations`), configurable via agent config.
- Request queue/backoff in `llm/request_queue.py`; retries in `llm/llm.py` using tenacity.
- Memory compression in `llm/memory_compressor.py` to stay within context limits.

## Maintenance
- Update module paths if files move; refresh diagram when flows change; align with CLI flag changes.
