# Strix Documentation Hub

Audience: AI and human developers extending Strix. Start here to find deep references, workflows, and extension guides.

- **Quick start**: see `docs/setup-and-running.md`.
- **Architecture**: high-level map in `docs/architecture.md`.
- **Agent loop**: internals in `docs/agent-loop.md`.
- **Tools**: contract and extensions in `docs/tools-and-extensions.md`.
- **Runtime**: sandbox and docker flow in `docs/runtime-and-sandbox.md`.
- **LLM config**: provider setup and tuning in `docs/llm-config.md`.
- **Prompts**: taxonomy and conventions in `docs/prompts.md`.
- **Interface**: CLI/TUI behaviors in `docs/interface.md`.
- **Telemetry**: tracing and events in `docs/telemetry-and-observability.md`.
- **Testing/QA**: strategies in `docs/testing-and-qa.md`.
- **Security/Privacy**: guardrails in `docs/security-and-privacy.md`.
- **Release**: versioning and publishing in `docs/release-and-versioning.md`.
- **Troubleshooting**: fixes in `docs/troubleshooting.md`.
- **Glossary**: definitions in `docs/glossary.md`.
- **Roadmap templates**: RFC/ADR formats in `docs/roadmap-templates.md`.

Minimum environment
- Python 3.12, Docker running, Playwright browsers installed.
- STRIX_LLM + LLM_API_KEY (or litellm proxy) exported.
- Local write access for `strix_runs/` outputs.

Flow for new contributors
1) Read `architecture.md` and `agent-loop.md` for mental model.  
2) Run a local scan following `setup-and-running.md`.  
3) Review `development.md` + `testing-and-qa.md` before changes.  
4) Extend tools/prompts/runtime using relevant docs.  
5) Update docs and add tests with every feature or bugfix.  

Maintenance
- Keep links valid when files move.  
- Update dependency minimums when `pyproject.toml` changes.  
- Refresh examples and flags when CLI/TUI arguments change.  
