# Documentation Build Plan (status)

Purpose: exhaustive task list to produce deep, high-fidelity docs that enable AI programmers to scale, extend, and debug Strix. Treat each section as a checklist—do not skip items.

## Foundations (do first)
- [T001] Map repository structure: `strix/agents`, `tools`, `runtime`, `llm`, `prompts`, `interface`, `telemetry`, `prompts/*`, `containers`, `.github`, `pyproject.toml`, `README.md`. **DONE**
- [T002] Inventory current configs: env vars, CLI flags, default limits, file outputs (`strix_runs/<run>`). **DONE**
- [T003] Note external dependencies: Docker requirements, Playwright install steps, LLM providers (OpenAI), litellm proxy, network expectations. **DONE**
- [T004] Capture testing stack: pytest, pytest-asyncio, coverage, lint/type tools (ruff, mypy, pyright, pylint, bandit), formatting (black, isort). **DONE**
- [T005] Establish terminology: run_name, agent loop, tool server, renderer, tracer, action schema, memory compression, request queue. **DONE**
- [T006] Decide doc style: concise sections, code refs with paths, short examples, tables for configs, ASCII diagrams. **DONE**

## docs/README.md
- [T007] Provide “start here” orientation, audience (AI devs), and links to all docs. **DONE**
- [T008] Include quick start flow: install, configure STRIX_LLM/LLM_API_KEY, run first scan, where outputs go. **DONE**
- [T009] Add dependency table and minimum versions. **DONE**

## docs/architecture.md
- [T010] High-level diagrams: data flow from CLI → agent loop → tools/runtime → LLM → telemetry. **DONE**
- [T011] Describe core modules and responsibilities with file paths. **DONE**
- [T012] Explain agent graph/orchestration, non-interactive mode, and how results are persisted. **DONE**
- [T013] Include sequence for a typical scan (targets discovery → planning → tool execution → reporting). **DONE**
- [T014] Call out extension seams (adding tools, prompts, telemetry events). **DONE**

## docs/setup-and-running.md
- [T015] Local setup: Python 3.12, Poetry/pipx install, Playwright install command, Docker prerequisites. **DONE**
- [T016] Environment variables: STRIX_LLM, LLM_API_KEY, optional provider settings; defaults and examples. **DONE**
- [T017] Running modes: interactive TUI vs non-interactive (`-n`), multiple targets, instructions flag. **DONE**
- [T018] Run outputs: structure of `strix_runs/`, logs, reports. **DONE**
- [T019] Common install pitfalls and fixes. **DONE**

## docs/development.md
- [T020] Repository layout primer. **DONE**
- [T021] Coding standards: typing requirements, lint/format commands, pre-commit guidance. **DONE**
- [T022] How to run tests (unit/integration) and coverage. **DONE**
- [T023] Contribution workflow: branching, PR expectations, CI checks, code owners if any. **DONE**
- [T024] Performance tips (caching models, reducing docker churn). **DONE**

## docs/agent-loop.md
- [T025] Detail `strix/agents/base_agent.py`, `state.py`, and `StrixAgent/strix_agent.py` lifecycle. **DONE**
- [T026] Explain state machine, max iterations, memory compression, request queue/backoff, tool selection loop. **DONE**
- [T027] Document hooks/callbacks and error handling patterns. **DONE**
- [T028] Show how vulnerability findings propagate to tracer/UI. **DONE**

## docs/tools-and-extensions.md
- [T029] Describe tool contract: action schemas (`*_actions_schema.xml`), implementations, registration (`tools/registry.py`). **DONE**
- [T030] Document each tool folder purpose (browser, proxy, terminal, file_edit, python, reporting, notes, thinking, finish, agents_graph). **DONE**
- [T031] Explain renderer pairing (`interface/tool_components/*`) and how UI consumes tool outputs. **DONE**
- [T032] Step-by-step for adding a new tool: schema, implementation, registry, renderer, tests. **DONE**
- [T033] Note safeguards for execution (timeouts, resource limits). **DONE**

## docs/runtime-and-sandbox.md
- [T034] Explain `runtime/docker_runtime.py`, `runtime/tool_server.py`, lifecycle of containerized actions. **DONE**
- [T035] Security boundaries: what is sandboxed, what is exposed, volume mounts, networking. **DONE**
- [T036] Configurable parameters (image, timeouts, resource limits) and where set. **DONE**
- [T037] Troubleshooting common runtime failures (docker not running, permissions, image pulls). **DONE**

## docs/llm-config.md
- [T038] Cover `llm/config.py`, `llm/llm.py`, request queue, retries/backoff (tenacity), streaming options. **DONE**
- [T039] Model selection guidance, cost/latency tuning, parallelism. **DONE**
- [T040] Provider-specific notes (OpenAI via litellm proxy) and how to add a new provider. **DONE**
- [T041] Logging/telemetry of LLM calls and redaction practices. **DONE**

## docs/prompts.md
- [T042] Taxonomy: frameworks, technologies, vulnerabilities, coordination, root agent prompt, system prompts. **DONE**
- [T043] Jinja template conventions and variables; how prompts are selected/combined. **DONE**
- [T044] Safe-testing prompts: dry runs, guardrails, and regression considerations when editing. **DONE**
- [T045] Adding a new prompt pack (file location, naming, validation). **DONE**

## docs/interface.md
- [T046] Describe CLI entrypoints (`interface/main.py`, `cli.py`), argument parser, flags. **DONE**
- [T047] TUI layout (`tui.py`), key panels, live stats rendering (`utils.py`), vulnerability display. **DONE**
- [T048] Non-interactive mode behavior and output formatting. **DONE**
- [T049] Customization hooks (colors/styles via `interface/assets/tui_styles.tcss`). **DONE**

## docs/telemetry-and-observability.md
- [T050] Detail tracer API (`telemetry/tracer.py`), emitted events, vulnerability callbacks. **DONE**
- [T051] How telemetry is persisted/consumed; how to add new spans/fields. **DONE**
- [T052] Guidance for integrating with external observability stacks (logs/metrics exports if available). **DONE**

## docs/testing-and-qa.md
- [T053] Test pyramid: unit (per module), integration (tool + runtime), e2e (sample scans). **DONE**
- [T054] Fixtures and test targets (dockerized apps if any); how to craft deterministic inputs. **DONE**
- [T055] Browser/Playwright tool checks; proxy and terminal tool validation. **DONE**
- [T056] Regression checklist when adding tools/prompts/runtime changes. **DONE**

## docs/security-and-privacy.md
- [T057] Secret handling (env vars), redaction expectations, LLM data minimization. **DONE**
- [T058] Threat model for running against untrusted targets; sandboxing caveats. **DONE**
- [T059] Network/file system safety defaults, user consent boundaries. **DONE**
- [T060] Supply chain concerns (pip/poetry deps, docker images). **DONE**

## docs/release-and-versioning.md
- [T061] Versioning scheme (current 0.4.0), how to bump, changelog expectations. **DONE**
- [T062] Packaging steps (poetry build/publish), PyPI notes, release artifact checklist. **DONE**
- [T063] Compatibility guarantees (Python 3.12 only) and deprecation policy. **DONE**

## docs/troubleshooting.md
- [T064] Common issues: LLM timeouts, invalid API key, docker daemon down, Playwright missing, port conflicts. **DONE**
- [T065] Observable symptoms, log locations, quick resolutions. **DONE**
- [T066] Decision tree for escalating issues. **DONE**

## docs/glossary.md
- [T067] Concise definitions for project terms, linked to code paths where applicable. **DONE**

## docs/roadmap-templates.md
- [T068] Provide RFC/ADR template and backlog template tailored to agents/tools/prompts/runtime changes. **DONE**
- [T069] Include evaluation criteria (security impact, latency, cost, UX). **DONE**

## Cross-cutting tasks
- [T070] Add code path references (`path:line` where helpful) and short code snippets for tricky parts. **DONE**
- [T071] Include minimal diagrams (ASCII ok) for data flow and agent loop. **DONE**
- [T072] Provide example commands for every procedure (setup, run, test, release). **DONE**
- [T073] Ensure all docs interlink; avoid duplication by linking to source doc sections. **DONE**
- [T074] Add “maintenance” note in each doc: when to update, owners if known. **DONE**

## Verification
- [T075] Pass through all docs for consistency of terms and flags. **DONE**
- [T076] Validate commands on a fresh environment (documented assumptions). **TODO – run on clean machine to verify every command and flag.**
- [T077] Spellcheck and lint Markdown if available. **TODO – run markdown lint/spellcheck pass.**
