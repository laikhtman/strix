# Telegram Bot Design Questions (with suggested options)

Answer these to lock UX and structure choices.

1) Transport mode?  
- [x] A) Webhook: stable and low-latency; requires public ingress/HTTPS endpoint and cert handling.  
- [ ] B) Long-polling: simplest (no ingress/certs), but slightly higher latency and less efficient at scale.  
- Recommendation: A (webhook) if ingress available; otherwise B.

2) Telegram library?  
- [ ] A) python-telegram-bot: mature, batteries-included, good docs; synchronous + async support.  
- [x] B) aiogram: fully async, performant, modular; leaner API, good for high throughput.  
- [ ] C) Other: specify if you prefer another ecosystem (e.g., Telethon) with trade-offs.  
- Recommendation: B (aiogram) for async throughput; A if you want maximal examples/docs.

3) Authentication/authorization?  
- [x] A) Allowlisted user IDs: simplest hard gate; manage allowed IDs in config/secret.  
- [ ] B) Shared secret/passphrase + allowlist: extra challenge step to join; good for small teams.  
- [ ] C) Org invite flow: needs backing service/DB to manage org membership; most overhead.  
- [ ] D) No auth: fastest but insecure; not recommended.  
- Recommendation: B (secret + allowlist) for extra friction; A if single-user.

4) Hosting model?  
- [x] A) Sidecar container with Strix: co-located, easy FS access to `strix_runs`, simple networking.  
- [ ] B) Separate microservice: clean separation, can scale independently; needs API into Strix.  
- [ ] C) Single binary embedding Strix: lowest moving parts, but couples release cycles tightly.  
- Recommendation: A (sidecar) to simplify FS access and reduce latency.

5) Strix control interface for bot?  
- [ ] A) Wrap CLI invocations: minimal code change; slower startup per run; manage subprocess IO.  
- [x] B) Internal Python API: direct calls; faster, richer control; requires stable internal surface.  
- [ ] C) Lightweight HTTP API: bot calls a service exposing run control; clearer boundaries, extra service to maintain.  
- Recommendation: B for performance and richness; C if you want clearer service boundary.

6) Command style?  
- [ ] A) Slash commands only: clear and predictable; more typing, fewer affordances.  
- [x] B) Slash commands + inline keyboards: best UX; quick actions, contextual buttons.  
- [ ] C) Menu-driven persistent buttons: fewer typed commands; more state/UI logic to maintain.  
- Recommendation: B for balance of clarity and UX.

7) Output verbosity to chat?  
- [ ] A) Only high-severity + summaries: low noise, risk missing context.  
- [ ] B) All vulns batched: balanced signal/noise; periodic bundles.  
- [ ] C) Full live stream (logs + vulns): maximum visibility; noisy and rate-limit prone.  
- [x] D) Toggle per-run: user chooses verbosity per run; most flexible.  
- Recommendation: D to let user choose per run.

8) Report delivery format?  
- [ ] A) Send full report file: one-step access; may hit Telegram size limits; compress if needed.  
- [x] B) Summary + on-demand file: keeps chat light; user pulls full report when desired.  
- [ ] C) Download link only: minimal bot bandwidth; depends on external hosting/ingress.  
- Recommendation: B (summary + on-demand) to manage size/noise.

9) `strix_runs` browsing UX?  
- [x] A) List runs then drill via buttons: guided, low error risk; limited flexibility.  
- [ ] B) Free-form path requests: powerful for power-users; risk of typos/path traversal (must sanitize).  
- [ ] C) Search first (target/date/severity), then browse: scalable when many runs; extra steps.  
- Recommendation: A with search filter add-on if run count grows.

10) Resume capability?  
- [x] A) Support resume if pausable; otherwise fall back to read-only with clear messaging.  
- [ ] B) Review-only: simplest; avoids partial state issues but no resume.  
- Recommendation: A if resume is feasible; otherwise B until resume exists.

11) Docs access from bot?  
- [ ] A) `/docs <topic>` sends excerpt + file link: explicit pull model.  
- [ ] B) Inline suggestions after errors: proactive help; avoid spam with throttling.  
- [x] C) Both: best UX; needs guardrails to prevent noisy suggestions.  
- Recommendation: C with throttling and opt-out toggle.

12) Rate limiting and batching?  
- [x] A) Global limits + severity filters: easy to manage; prevents floods.  
- [ ] B) Per-user limits: fair sharing in multi-user scenarios.  
- [ ] C) No limits: simplest but risky; can spam chats and hit Telegram limits.  
- Recommendation: A (global + severity) plus optional per-user caps if multi-user.

13) Data sensitivity handling?  
- [x] A) Redact secrets by default; explicit `/send-sensitive` override: safest default.  
- [ ] B) Trust operator; send everything: fastest but riskier; rely on allowlist.  
- Recommendation: A to stay safe by default.

14) Observability for bot?  
- [ ] A) Structured logs only: minimal.  
- [x] B) Logs + metrics (commands, errors, latency): better insight; needs metrics backend.  
- [ ] C) Logs + metrics + alerting on delivery/API failures: best resilience; more setup.  
- Recommendation: B to start; grow to C if SLOs matter.

15) Persistence layer for bot state?  
- [ ] A) In-memory: trivial; loses pagination/state on restart.  
- [x] B) SQLite/bolt: easy local persistence; good for single instance.  
- [ ] C) Redis: shared state for HA, fast; needs service.  
- [ ] D) Postgres/DB: full durability and querying; more ops overhead.  
- Recommendation: B for simplicity; C if you need HA.

16) Deployment target?  
- [ ] A) Docker/k8s with CI: standard, repeatable, scalable.  
- [x] B) VM/systemd: simple if infra is minimal; manual care.  
- [ ] C) Local/dev-only: fastest to iterate; not suitable for prod use.  
- Recommendation: A if you already use containers; B for quick internal deploys.

17) Error handling UX?  
- [ ] A) Friendly error + suggested next command: best guidance.  
- [x] B) Minimal error: terse; less helpful.  
- [ ] C) Auto-retry then notify on failure: smoother UX; needs idempotent handlers.  
- Recommendation: C with a cap on retries and A-style guidance on failure.
