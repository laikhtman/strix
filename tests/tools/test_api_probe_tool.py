from pathlib import Path

from strix.tools.api_probe.api_probe_actions import load_openapi_spec, suggest_api_fuzz_cases


def test_load_openapi_spec_parses_endpoints(tmp_path: Path) -> None:
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}
                    ],
                }
            }
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(__import__("json").dumps(spec), encoding="utf-8")

    result = load_openapi_spec(str(spec_path))
    endpoints = result["endpoints"]

    assert endpoints[0]["path"] == "/users"
    assert endpoints[0]["method"] == "GET"
    assert endpoints[0]["params"][0]["name"] == "limit"


def test_suggest_api_fuzz_cases_generates_payloads() -> None:
    endpoints = [{"path": "/users", "method": "GET", "params": [{"name": "id"}]}]

    result = suggest_api_fuzz_cases(endpoints)

    assert result["suggestions"][0]["payloads"][0]["name"] == "id"
