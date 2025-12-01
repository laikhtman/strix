# Testing and QA

## Stack
- Unit/integration tests via `pytest`, async via `pytest-asyncio`.
- Coverage via `pytest --cov`.
- Static checks: `ruff`, `mypy`, `pyright`, `pylint`, `bandit`.

## Strategy
- Unit: isolate modules (LLM utils, request queue, memory compressor, tracer, tool registry).
- Integration: tool + runtime interactions (browser/proxy/terminal/python actions) in sandbox.
- E2E: run `strix -n --target <fixture>` against known targets; assert vulnerability outputs/logs.

## Fixtures
- Prefer dockerized test targets for determinism; keep small for fast runs.
- Mock LLM responses when testing agent logic to avoid network cost.

## Regression checklist
- Tool changes: schema + renderer tests, action behavior, sandbox safety.
- Prompt changes: render tests to ensure variables resolved and key guidance present.
- Runtime changes: container lifecycle tests and timeout behavior.
- Interface changes: argument parsing and renderer output snapshots where feasible.

## Commands
```bash
poetry run pytest
poetry run pytest --cov
poetry run ruff check .
poetry run mypy .
poetry run pyright
```

## Maintenance
- Update when test fixtures or target apps change; keep command list aligned with tooling versions.
