# Strix Product Roadmap (AI-operator focused)

Goal: Make Strix more powerful, scalable, and operator-friendly for AI programmers and security teams.

Legend: [ ] pending, [~] in progress, [x] done

## Core Agent & Orchestration
- [x] A01: Pluggable agent graph builder (YAML/JSON) to compose multi-agent workflows with validation. (Standalone) Added schema/loader in strix/agents/graph_builder.py with validation + tests/agents/test_graph_builder.py; supports JSON and optional YAML; documented in docs/architecture.md.
- [x] A02: Adaptive iteration limits based on target complexity and model latency; expose telemetry. (Standalone) Added iteration budget helper (strix/agents/iteration_policy.py) and wired CLI/TUI/bot to set max_iterations + tracer metadata; BaseAgent records policy; updated docs/agent-loop.md.
- [x] A03: Resumeable agent state (persist tool queue, memory, tracer) to survive restarts. (Standalone) Added AgentState save/load helpers and BaseAgent persistence hooks (state snapshots to run dir); tests/agents/test_state_persistence.py; documented in docs/agent-loop.md.
- [ ] A04: Strategy presets (aggressive/exploratory/compliance) selectable via CLI/bot flags. (Depends: A01)
- [ ] A05: Memory management improvements (hierarchical summarization, eviction policy tuning). (Standalone)
- [ ] A06: Action budget guardrail (tokens/time/tool invocations) per run with overrides and reporting. (Standalone)
- [ ] A07: Agent self-evaluation prompts to prune bad tool paths and refocus on target goals. (Standalone)
- [ ] A08: Multi-model consensus mode to reduce hallucinations for high-risk findings. (Standalone)

## Tooling & Coverage
- [x] T01: Add SAST/dep scanning tool (e.g., Semgrep/Trivy) with parsers into unified findings. (Standalone) Added SAST/deps tool (strix/tools/sast/*), registry wiring, docs/tools-and-extensions.md, and tests (tests/tools/test_sast_tool.py).
- [x] T02: Browser automation enhancements (network capture/har timing, screenshot diffs). (Standalone) Added network logging + screenshot diff in browser tool (browser_instance/tab_manager/browser_actions/schema); new actions get_network_events/capture_screenshot_diff.
- [x] T03: API probing tool (OpenAPI/Swagger ingestion, auth flows, fuzzing of endpoints). (Standalone) Added OpenAPI loader + fuzz suggestion tool (strix/tools/api_probe/*), registry wiring, docs/tools-and-extensions.md, tests/tools/test_api_probe_tool.py.
- [x] T04: Auth-focused playbooks (OIDC/SAML/SSO) with reusable prompt/tool bundles. (Standalone) Added auth playbook prompt module (strix/prompts/auth/oidc_saml_sso.jinja) + docs/prompts.md and tests/prompts/test_auth_playbook_prompt.py.
- [x] T05: Reporting enrichment (CVSS estimation, fix-by snippets, references to CWE/OWASP). (Standalone) Reporting tool now accepts CVSS/fix/references/CWE metadata (reporting_actions/schema, tracer persistence, SARIF/CSV/JSONL); docs/tools-and-extensions.md; tests/tools/test_reporting_enrichment.py.
- [x] T06: Structured finding export (SARIF/JSONL) for CI upload. (Standalone) Added JSONL vulnerability export and SARIF 2.1.0 writer in tracer save_run_data/_build_sarif_report (strix/telemetry/tracer.py); tuned SARIF driver metadata to avoid assumed URLs and normalized runName serialization; documented structured exports in docs/telemetry-and-observability.md and docs/setup-and-running.md; validated end-to-end via tracer run output.
- [ ] T07: Offline mode with cached model responses (for deterministic regression fixtures). (Depends: A03)
- [ ] T08: Advanced redaction policies (PII, keys, JWTs) configurable per run. (Standalone)
- [ ] T09: Prompted codegen tool for quick patch proposals with diff output. (Standalone)
- [ ] T10: Auto-target discovery (sitemaps/robots/crawling) feeding agent planning. (Standalone)
- [ ] T11: Secrets exfil detection tool (simulate attacker to validate data exposure). (Standalone)
- [ ] T12: Mobile/API auth testing harness (JWT/PKCE/refresh token misuse checks). (Standalone)

## Performance & Scale
- [ ] P01: Concurrent multi-target orchestration with resource budgeting per target. (Standalone)
- [ ] P02: Model multiplexing (primary/backoff) with cost/latency-aware routing. (Standalone)
- [ ] P03: Caching layer for repeated tool outputs (fingerprint by target + action). (Standalone)
- [ ] P04: Parallel tool server pool with auto-scaling (containers) and health checks. (Standalone)
- [ ] P05: Benchmark suite against standard targets; publish latency/cost baselines. (Standalone)
- [ ] P06: Warm pool for LLM sessions to reduce cold-start latency on first calls. (Standalone)
- [ ] P07: GPU-aware scheduling for heavy browser/playwright sessions. (Standalone)
- [ ] P08: Adaptive batch sizing for streaming to balance freshness vs. rate limits. (Standalone)

## Observability & Safety
- [ ] O01: Structured logging across agent, tools, and bot with trace/run IDs. (Standalone)
- [ ] O02: Metrics exporter (Prometheus/OpenTelemetry) covering runs, tools, errors, latency, cost. (Standalone)
- [ ] O03: Alerting rules for failures (LLM errors, tool crashes, delivery issues). (Depends: O02)
- [ ] O04: Audit trail for tool invocations and file writes (tamper-evident). (Standalone)
- [ ] O05: Policy engine to gate risky actions (write/exec) with user/bot confirmations. (Standalone)
- [ ] O06: User-facing run timeline view with step durations and tool outcomes. (Depends: O01)
- [ ] O07: PII/secret leak detector on outbound LLM/tool payloads with block/allow overrides. (Standalone)
- [ ] O08: Cost dashboard per run/target with model/tool breakdown. (Depends: O02)

## UX: CLI/TUI
- [ ] U01: CLI presets and config profiles (YAML) for repeatable runs. (Standalone)
- [ ] U02: Rich TUI logs with search, filters, and jump-to finding. (Standalone)
- [ ] U03: Interactive remediation mode (apply suggested patches with confirm/rollback). (Depends: T09)
- [ ] U04: Better non-interactive output (JSON schema stable, machine-consumable). (Standalone)
- [ ] U05: Inline links to docs and playbooks from CLI/TUI errors. (Standalone)
- [ ] U06: Export TUI session transcript (with redaction) for sharing/debugging. (Standalone)
- [ ] U07: Colorblind-friendly themes and accessibility pass for TUI/CLI output. (Standalone)
- [ ] U08: CLI wizard for first-time setup (env validation, sample run). (Standalone)

## UX: Telegram Bot & Integrations
- [ ] B01: Webhook IP allowlist enforcement and bot feature flags. (Standalone)
- [ ] B02: Web UI companion (read-only) for browsing runs/files/reports. (Standalone)
- [ ] B03: Slack/Teams adapter sharing bot command surface. (Standalone)
- [ ] B04: Scheduled reports to chat (daily/weekly summaries). (Standalone)
- [ ] B05: Quick actions for retrying failed tools or re-running with different presets. (Standalone)
- [ ] B06: Inline search for findings within a run (by severity/CWE/keyword). (Depends: D04)
- [ ] B07: Multi-target run creation from chat (comma-separated URLs) with per-target status buttons. (Standalone)
- [ ] B08: Bot command audit export (CSV/JSON) for compliance. (Depends: O04)

## Data & Storage
- [ ] D01: Run metadata store (SQLite/Postgres) with query API for targets, findings, timestamps. (Standalone)
- [ ] D02: Artifact retention policies (TTL, archiving to S3/Blob) and cleanup jobs. (Depends: D01)
- [ ] D03: Encrypted-at-rest option for `strix_runs` and secrets. (Standalone)
- [ ] D04: Deduplicated finding store across runs (fingerprints). (Depends: D01)
- [ ] D05: Incremental sync/backup of runs to object storage with integrity hashes. (Depends: D01)
- [ ] D06: Finding triage states (open/mitigated/false-positive) persisted and exported. (Depends: D01)
- [ ] D07: Data catalog of targets/runs with tagging (env/team/compliance level). (Depends: D01)

## Quality & Testing
- [ ] Q01: Golden-run fixtures for deterministic regression (mock LLM/tool responses). (Standalone)
- [ ] Q02: Integration tests per tool against canned targets. (Depends: T01–T12)
- [ ] Q03: Load tests for high-volume vuln streaming (bot + CLI). (Depends: P08)
- [ ] Q04: Chaos testing for tool-server and LLM outages. (Standalone)
- [ ] Q05: Benchmark-based CI gate (fail if latency/cost regress beyond thresholds). (Depends: P05)
- [ ] Q06: Property-based tests for tool schema validation and renderer pairing. (Standalone)
- [ ] Q07: Fuzzing inputs for API probing and file parsing tools. (Depends: T03, T12)
- [ ] Q08: Shadow-mode runs comparing new vs. stable prompts/tools before promotion. (Depends: A01)

## Docs & Developer Experience
- [ ] X01: Developer portal page linking all docs, playbooks, and templates. (Standalone)
- [ ] X02: ADR/RFC cadence with templates and review checklist. (Standalone)
- [ ] X03: “How to add a tool” quickstart with example PR and tests. (Depends: T01)
- [ ] X04: Migration guides for new model providers or runtime changes. (Standalone)
- [ ] X05: Troubleshooting decision trees per subsystem (LLM, tools, runtime, bot). (Standalone)
- [ ] X06: Cookbook of end-to-end recipes (e.g., “scan monolith web app”, “API-first target”, “SSO target”). (Standalone)
- [ ] X07: Video/animated walkthroughs for setup and first run. (Standalone)
- [ ] X08: Localization-ready docs structure for future translations. (Standalone)

## Security & Compliance
- [ ] S01: Threat model update including bot surface and webhook ingress. (Standalone)
- [ ] S02: Supply-chain scanning of dependencies and base images in CI. (Standalone)
- [ ] S03: Secrets scanning guard in repo and runtime paths. (Standalone)
- [ ] S04: Audit log export to SIEM (JSONL/OTLP). (Depends: O04)
- [ ] S05: RBAC for bot and API (per-command permissions). (Depends: D01)
- [ ] S06: mTLS option for webhook ingress and internal control API. (Standalone)
- [ ] S07: DLP hooks on report/file export (block sensitive data exfiltration). (Depends: D04)
- [ ] S08: Privacy mode to mask/redact target-identifying data in logs/streams. (Depends: O07)
