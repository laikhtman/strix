from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from strix.tools.registry import register_tool


_DANGEROUS_PATTERNS = [
    {
        "id": "PY001",
        "regex": r"\beval\(",
        "severity": "high",
        "message": "Use of eval() can lead to code execution",
    },
    {
        "id": "PY002",
        "regex": r"\bexec\(",
        "severity": "high",
        "message": "Use of exec() can lead to code execution",
    },
    {
        "id": "PY003",
        "regex": r"subprocess\.(run|Popen)\([^)]*shell\s*=\s*True",
        "severity": "high",
        "message": "subprocess with shell=True can lead to command injection",
    },
    {
        "id": "PY004",
        "regex": r"random\.(randrange|randint|random)\(",
        "severity": "medium",
        "message": "Insecure randomness; prefer secrets module for security tokens",
    },
]

_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox", ".ruff_cache"}


def _iter_code_files(base: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for path in base.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
        if len(files) >= max_files:
            break
    return files


@register_tool(sandbox_execution=False)
def run_sast_scan(target_path: str | None = None, max_files: int = 200) -> dict[str, Any]:
    base = Path(target_path or ".").resolve()
    findings: list[dict[str, Any]] = []

    for file_path in _iter_code_files(base, max_files):
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for pattern in _DANGEROUS_PATTERNS:
                if re.search(pattern["regex"], line):
                    findings.append(
                        {
                            "file": str(file_path),
                            "line": idx,
                            "rule_id": pattern["id"],
                            "severity": pattern["severity"],
                            "message": pattern["message"],
                            "snippet": line.strip(),
                        }
                    )
    return {"success": True, "findings": {"static": findings}}


@register_tool(sandbox_execution=False)
def scan_dependencies(target_path: str | None = None) -> dict[str, Any]:
    base = Path(target_path or ".").resolve()
    findings: list[dict[str, Any]] = []

    req_file = base / "requirements.txt"
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "==" not in stripped and ">=" not in stripped and "<=" not in stripped:
                findings.append(
                    {
                        "package": stripped,
                        "spec": "unpinned",
                        "severity": "medium",
                        "reason": "Dependency is not pinned; prefer exact versions",
                    }
                )

    pyproject = base / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for pkg, spec in deps.items():
                if pkg == "python":
                    continue
                if spec == "*" or spec == "^0.0.0":
                    findings.append(
                        {
                            "package": pkg,
                            "spec": str(spec),
                            "severity": "medium",
                            "reason": "Wildcard dependency version detected",
                        }
                    )
        except Exception:
            findings.append(
                {
                    "package": "unknown",
                    "spec": "parse_error",
                    "severity": "low",
                    "reason": "Unable to parse pyproject.toml for dependency checks",
                }
            )

    return {"success": True, "findings": {"dependencies": findings}}
