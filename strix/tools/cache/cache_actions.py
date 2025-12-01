from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strix.tools.registry import register_tool


CACHE_DIR = Path.cwd() / "strix_cache"


def _cache_path(target: str, action: str) -> Path:
    safe_target = target.replace("/", "_").replace(":", "_")
    safe_action = action.replace("/", "_")
    return CACHE_DIR / f"{safe_target}__{safe_action}.json"


@register_tool(sandbox_execution=False)
def cache_result(target: str, action: str, result: str) -> dict[str, Any]:
    CACHE_DIR.mkdir(exist_ok=True)
    path = _cache_path(target, action)
    path.write_text(result, encoding="utf-8")
    return {"success": True, "cached_path": str(path)}


@register_tool(sandbox_execution=False)
def get_cached_result(target: str, action: str) -> dict[str, Any]:
    path = _cache_path(target, action)
    if not path.exists():
        return {"success": False, "cached": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = path.read_text(encoding="utf-8")
    return {"success": True, "cached": True, "result": data}
