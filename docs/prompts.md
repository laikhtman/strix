# Prompts

## Taxonomy
- Coordination: `prompts/coordination/root_agent.jinja`
- Frameworks: `prompts/frameworks/*.jinja` (e.g., `fastapi`, `nextjs`)
- Technologies: `prompts/technologies/*.jinja` (e.g., `firebase_firestore`, `supabase`)
- Vulnerabilities: `prompts/vulnerabilities/*.jinja` (e.g., `sql_injection`, `xss`, `rce`)
- Auth playbooks: `prompts/auth/oidc_saml_sso.jinja`
- Cloud/custom/recon placeholders: `prompts/cloud`, `prompts/custom`, `prompts/reconnaissance`
- Agent system prompt: `agents/StrixAgent/system_prompt.jinja`

## Conventions
- Jinja templates with explicit placeholders; avoid hidden assumptions.
- Keep titles and sections consistent for downstream parsing.
- Prefer actionable guidance (steps, checks, PoC ideas) and explicit do/don’t lists.

## Selection/combination
- Agent selects relevant prompt packs based on target metadata; templates rendered via Jinja environment set in `AgentMeta`.
- Root coordination prompt guides multi-agent behavior; specialized prompts augment depending on framework/tech/vuln focus.

## Safe testing
- Dry-run new prompts in non-interactive mode against test targets.
- Check for prompt injection surfaces; ensure instructions avoid unsafe actions outside sandbox.
- Validate output format expected by tools (e.g., when tool calls must be produced).

## Adding a prompt pack
1) Create `.jinja` file in appropriate folder with descriptive name.
2) Document variables required; keep defaults sensible.
3) Add regression test or fixture to ensure rendering works and key strings exist.
4) Update this doc and any selection logic if needed.

## Maintenance
- Refresh taxonomy when adding/removing prompt packs; ensure variable names stay consistent with agent code.
