from pathlib import Path

from strix.tools.sast.sast_actions import run_sast_scan, scan_dependencies


def test_run_sast_scan_flags_eval(tmp_path: Path) -> None:
    suspicious = tmp_path / "app.py"
    suspicious.write_text("def run():\n    return eval('1+1')\n", encoding="utf-8")

    result = run_sast_scan(str(tmp_path))

    findings = result["findings"]["static"]
    assert any(f["rule_id"] == "PY001" for f in findings)
    assert findings[0]["file"].endswith("app.py")


def test_scan_dependencies_flags_unpinned_requirement(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("flask\nrequests>=2.0.0\n", encoding="utf-8")

    result = scan_dependencies(str(tmp_path))

    findings = result["findings"]["dependencies"]
    assert any(f["package"] == "flask" and f["spec"] == "unpinned" for f in findings)


def test_scan_dependencies_flags_wildcard_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.poetry]
name = "sample"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.12"
flask = "*"
""",
        encoding="utf-8",
    )

    result = scan_dependencies(str(tmp_path))
    findings = result["findings"]["dependencies"]
    assert any(f["package"] == "flask" for f in findings)
