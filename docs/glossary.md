# Glossary

- Agent loop: Iterative cycle in `agents/base_agent.py` driving LLM calls and tool executions.
- Agent graph: In-memory map of agents managed via `tools/agents_graph/agents_graph_actions.py`, rendered in UI.
- Action schema: XML definition (`*_actions_schema.xml`) describing tool actions/args.
- Renderer: UI component in `interface/tool_components/*` mapping tool outputs to panels.
- Runtime: Docker-based sandbox managed by `runtime/docker_runtime.py` and `tool_server.py`.
- Tracer: Telemetry recorder in `telemetry/tracer.py` logging agent and tool events.
- Run name: Unique id for a scan; names output directory `strix_runs/<run_name>`.
- Request queue: LLM request coordinator in `llm/request_queue.py`.
- Memory compressor: Context trimming utility in `llm/memory_compressor.py`.
- Non-interactive mode: Headless CLI mode (`-n`) emitting findings to stdout without TUI.

## Maintenance
- Add new terms as components are introduced; keep paths accurate after refactors.
