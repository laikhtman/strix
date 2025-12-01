from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List

from .control_api import ControlAPI, RunInfo


class FileSystemControlAPI(ControlAPI):
    """
    File-system backed control API for read-only operations on existing runs.
    Start/stop/resume are not implemented here and should be wired to Strix internals.
    """

    def __init__(self, root_path: str | Path = ".", cache_ttl: float = 10.0) -> None:
        self.root_path = Path(root_path).resolve()
        self.runs_dir = self.root_path / "strix_runs"
        self.cache_ttl = cache_ttl
        self._runs_cache: list[RunInfo] = []
        self._runs_cache_ts: float = 0.0

    def _run_path(self, run_id: str) -> Path:
        return (self.runs_dir / run_id).resolve()

    def _safe_path(self, run_id: str, subpath: str = "") -> Path:
        base = self._run_path(run_id)
        target = (base / subpath).resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("Invalid path")
        return target

    def start_run(
        self,
        target: str,
        instruction: str | None = None,
        verbosity: str | None = None,
        stream_callback: Optional[Callable[[str, str, str, str], None]] = None,
    ) -> RunInfo:
        raise NotImplementedError("Start run not implemented in FileSystemControlAPI.")

    def list_runs(self, limit: int = 20) -> List[RunInfo]:
        now = time.monotonic()
        if self._runs_cache and now - self._runs_cache_ts < self.cache_ttl:
            return self._runs_cache[:limit]

        if not self.runs_dir.exists():
            return []
        entries = [
            (p, p.stat().st_mtime)
            for p in self.runs_dir.iterdir()
            if p.is_dir()
        ]
        entries.sort(key=lambda x: x[1], reverse=True)
        runs: list[RunInfo] = []
        for path, _ in entries[:limit]:
            runs.append(
                RunInfo(
                    run_id=path.name,
                    target="unknown",
                    status="unknown",
                )
            )
        self._runs_cache = runs
        self._runs_cache_ts = now
        return runs

    def get_run_info(self, run_id: str) -> RunInfo | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        return RunInfo(run_id=run_id, target="unknown", status="unknown")

    def tail_logs(self, run_id: str, offset: int = 0, limit: int = 200) -> List[str]:
        path = self._safe_path(run_id)
        log_candidates = [
            path / "stdout.log",
            path / "logs.txt",
            path / "log.txt",
            path / "run.log",
        ]
        log_file = next((p for p in log_candidates if p.exists()), None)
        if not log_file:
            return []
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines[offset: offset + limit]]

    def get_report_summary(self, run_id: str) -> str:
        path = self._safe_path(run_id)
        candidates = [
            path / "report.txt",
            path / "report.md",
            path / "report.html",
        ]
        report_file = next((p for p in candidates if p.exists()), None)
        if not report_file:
            return ""
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return content[:4000]

    def get_report_file(self, run_id: str) -> str | None:
        path = self._safe_path(run_id)
        candidates = [
            path / "report.txt",
            path / "report.md",
            path / "report.html",
            path / "report.json",
            path / "report.pdf",
        ]
        report_file = next((p for p in candidates if p.exists()), None)
        return str(report_file) if report_file else None

    def get_file_metadata(self, run_id: str, path: str) -> tuple[str, int] | None:
        file_path = self._safe_path(run_id, path)
        if not file_path.exists() or not file_path.is_file():
            return None
        return str(file_path), file_path.stat().st_size

    def list_files(self, run_id: str, path: str = "") -> List[Dict[str, Any]]:
        base = self._safe_path(run_id, path)
        if not base.exists() or not base.is_dir():
            return []
        results: list[Dict[str, Any]] = []
        for entry in base.iterdir():
            results.append(
                {
                    "name": entry.name,
                    "path": os.path.relpath(entry, self._run_path(run_id)),
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size,
                }
            )
        return results

    def read_file(self, run_id: str, path: str) -> bytes:
        file_path = self._safe_path(run_id, path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError("File not found")
        return file_path.read_bytes()

    def resume_run(self, run_id: str) -> bool:
        raise NotImplementedError("Resume not implemented in FileSystemControlAPI.")

    def stop_run(self, run_id: str) -> bool:
        raise NotImplementedError("Stop not implemented in FileSystemControlAPI.")
