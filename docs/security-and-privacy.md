# Security and Privacy

## Secrets and data handling
- Use env vars for provider keys (`STRIX_LLM`, `LLM_API_KEY`); avoid hardcoding.
- Redact sensitive content before telemetry/logging; tracer extensions should strip secrets.

## Threat model
- Targets may be untrusted; sandbox all active tooling via docker runtime.
- Limit volume mounts to required paths; constrain network access where possible.
- Validate tool inputs; sanitize file paths and URLs from LLM output.

## Sandbox caveats
- Misconfigured docker (privileged mounts) can weaken isolation; review `runtime/docker_runtime.py` changes carefully.
- Browser/proxy tools can reach external hosts; ensure user consent and scope limitations.

## Supply chain
- Pin dependencies in `pyproject.toml`; review updates for security impact.
- Verify docker images and registries; avoid pulling untrusted images.

## Privacy
- Minimize data sent to LLMs; prefer summaries over raw sensitive payloads.
- Provide users clarity on what leaves the machine when using remote providers.

## Maintenance
- Revisit threat model when runtime/networking or tool capabilities change; ensure redaction guidance matches telemetry behavior.
