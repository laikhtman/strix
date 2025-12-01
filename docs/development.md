# Development Guide

## Layout primer
- Core agent logic: `strix/agents/*`
- Tools and action schemas: `strix/tools/*`
- Runtime sandbox: `strix/runtime/*`
- LLM layer: `strix/llm/*`
- Prompts: `strix/prompts/*` and `strix/agents/StrixAgent/system_prompt.jinja`
- Interface (CLI/TUI + renderers): `strix/interface/*`
- Telemetry: `strix/telemetry/*`

## Standards
- Python 3.12, strict typing (see `pyproject.toml` mypy config).
- Lint/format: `ruff`, `black`, `isort`.
- Security/static: `bandit`, `pylint`.
- Keep docstrings concise; prefer clear variable names over comments.

## Commands
```bash
# Format + lint
poetry run ruff check .
poetry run black .
poetry run isort .

# Type check
poetry run mypy .
poetry run pyright

# Tests
poetry run pytest
poetry run pytest --cov
```

## Workflow
- Create feature branches; keep commits scoped.
- Run format + lint + tests before PR.
- Update relevant docs when changing behavior, flags, prompts, or outputs.
- Add regression coverage for new tools/prompt changes/runtime adjustments.

## Performance tips
- Reuse docker images; avoid repeated pulls.
- Cache provider auth where possible; tune LLM parallelism in config.
- Use smaller prompt packs for targeted testing when iterating quickly.

## Maintenance
- Revise commands/tools when linters/types/test stacks change; align with `pyproject.toml`.
