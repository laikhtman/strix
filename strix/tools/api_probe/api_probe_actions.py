from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strix.tools.registry import register_tool


def _load_spec(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError("PyYAML required for YAML specs; install pyyaml") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    return json.loads(path.read_text(encoding="utf-8"))


def _extract_type(param: dict[str, Any]) -> str:
    schema = param.get("schema", {})
    if "type" in schema:
        return str(schema["type"])
    if "$ref" in schema:
        return "object_ref"
    return "unknown"


@register_tool(sandbox_execution=False)
def load_openapi_spec(spec_path: str) -> dict[str, Any]:
    spec = _load_spec(Path(spec_path))
    paths = spec.get("paths", {})
    endpoints: list[dict[str, Any]] = []

    for path, methods in paths.items():
        for method, details in methods.items():
            params = []
            for p in details.get("parameters", []):
                params.append(
                    {
                        "name": p.get("name"),
                        "in": p.get("in"),
                        "required": p.get("required", False),
                        "type": _extract_type(p),
                    }
                )
            endpoints.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "params": params,
                }
            )

    return {"success": True, "endpoints": endpoints}


@register_tool(sandbox_execution=False)
def suggest_api_fuzz_cases(endpoints: list[dict[str, Any]]) -> dict[str, Any]:
    fuzz_strings = [
        "' OR '1'='1",
        "\"; DROP TABLE users; --",
        "../../etc/passwd",
        "${{7*7}}",
        "<script>alert(1)</script>",
    ]

    suggestions = []
    for ep in endpoints:
        param_payloads = []
        for param in ep.get("params", []):
            param_payloads.append({"name": param.get("name"), "payload": fuzz_strings[0]})
        suggestions.append(
            {
                "path": ep.get("path"),
                "method": ep.get("method"),
                "payloads": param_payloads or [{"payload": fuzz_strings[1]}],
            }
        )

    return {"success": True, "suggestions": suggestions}
