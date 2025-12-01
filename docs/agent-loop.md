# Agent Loop Internals

Primary files: `agents/base_agent.py`, `agents/state.py`, `agents/StrixAgent/strix_agent.py`, `agents/StrixAgent/system_prompt.jinja`.

## Lifecycle
1) Agent instantiated with config: llm config, max iterations (default 300), non-interactive flag, optional state/local sources.
2) `AgentMeta` wires Jinja environment per agent folder for prompts.
3) `AgentState` tracks messages, tasks, wait states, agent graph ids.
4) Main loop (in `BaseAgent.run`): fetches/creates state, processes queued messages, updates tracer, calls LLM with prompt, dispatches tool invocations, handles waits/finishes.
5) Completion when finish tool invoked, max iterations hit, or fatal error.

## Message handling
- Messages stored in `AgentState`; inter-agent messages include metadata and are added as user messages with delivery notice.
- Tracer updates agent status on message receipt/resume.

## Tool selection and execution
- LLM output parsed for tool calls → `tools.process_tool_invocations` → `tools/executor.py`.
- Tool executions logged via tracer, results added back into state/context for next iteration.

## Memory and limits
- `llm/memory_compressor.py` trims context to fit provider limits.
- `llm/request_queue.py` manages concurrency/ordering; `llm/llm.py` handles retries/backoff (tenacity).
- Configurable `max_iterations` per agent instance via config.

## Error handling
- LLM errors wrapped in `LLMRequestFailedError`; retries applied.
- Tool errors logged and surfaced in state; agents can adapt prompts accordingly.

## Vulnerability propagation
- Tracer `vulnerability_found_callback` (set in CLI) renders findings immediately; tracer records IDs, severity, content.

## Extending the agent
- Adjust prompts in `agents/StrixAgent/system_prompt.jinja`.
- Modify decision logic in `StrixAgent/strix_agent.py`.
- Add new state fields carefully; ensure serialization if persisted; update tracer calls to include new metadata.

## ASCII loop snapshot
```
State -> Prompt render -> LLM -> Tool calls -> Results -> State update
   ^                                                   |
   +--------------------Tracer/events------------------+
```

## Maintenance
- Revise when state fields or loop control change; keep diagram aligned with actual steps; update when new hooks are added.
