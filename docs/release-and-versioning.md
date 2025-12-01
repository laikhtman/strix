# Release and Versioning

Current version: 0.4.0 (`pyproject.toml`).

## Versioning
- Follow semantic-ish bumps: increment patch for fixes, minor for features, major for breaking changes.
- Update `pyproject.toml` version and any surfaced docs.

## Packaging
```bash
poetry build
poetry publish  # requires credentials
```
- Ensure `README.md` and license included (listed in `[tool.poetry]` include).
- Verify wheels/sdist contain `.jinja`, `.xml`, `.tcss` assets (declared in `include`).

## Changelog
- Maintain a changelog (add file if missing) summarizing features, fixes, breaking changes.
- Reference PRs/issues; highlight security-impacting changes.

## Compatibility
- Python 3.12 only (per `pyproject.toml`).
- Document any deprecated flags or behaviors and provide migration notes.

## Maintenance
- Update version numbers and commands when packaging flow changes; ensure asset include lists stay correct.
