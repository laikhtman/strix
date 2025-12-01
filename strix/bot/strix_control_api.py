from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from strix.interface.main import build_targets_info  # type: ignore
from strix.interface.utils import generate_run_name  # type: ignore
from strix.llm.config import LLMConfig
from strix.telemetry.tracer import Tracer, set_global_tracer

from strix.agents.StrixAgent import StrixAgent
from strix.agents.iteration_policy import calculate_iteration_budget
from .control_api import ControlAPI, RunInfo

logger = logging.getLogger(__name__)


class StrixControlAPI(ControlAPI):
    """
    Control API that starts Strix runs via internal interfaces.
    Note: stop/resume/status are minimal; enhance with runtime hooks.
    """

    def __init__(self, root_path: str | Path = ".") -> None:
        self.root_path = Path(root_path).resolve()
        self.runs_dir = self.root_path / "strix_runs"
        self.active: Dict[str, dict[str, Any]] = {}

    def start_run(
        self,
        target: str,
        instruction: str | None = None,
        verbosity: str | None = None,
        stream_callback: Optional[Callable[[str, str, str, str], None]] = None,
    ) -> RunInfo:
        run_name = generate_run_name()
        targets_info = build_targets_info([target])
        scan_config = {
            "scan_id": run_name,
            "targets": targets_info,
            "user_instructions": instruction or "",
            "run_name": run_name,
        }
        tracer = Tracer(run_name)
        tracer.set_scan_config(scan_config)
        set_global_tracer(tracer)

        if stream_callback:
            def vuln_handler(report_id: str, title: str, content: str, severity: str) -> None:
                try:
                    stream_callback(report_id, title, content, severity)
                except Exception:  # noqa: BLE001
                    logger.exception("Stream callback failed")

            tracer.vulnerability_found_callback = vuln_handler

        llm_config = LLMConfig()
        iteration_policy = calculate_iteration_budget(targets_info, llm_config.timeout)
        agent_config = {
            "llm_config": llm_config,
            "max_iterations": iteration_policy["max_iterations"],
            "iteration_policy": iteration_policy,
            "non_interactive": True,
        }
        tracer.set_iteration_policy(iteration_policy)
        agent = StrixAgent(agent_config)

        async def runner() -> None:
            try:
                await agent.run()
                if run_name in self.active:
                    self.active[run_name]["status"] = "completed"
                    self.active[run_name]["ended_at"] = datetime.utcnow().isoformat()
            except Exception:  # noqa: BLE001
                logger.exception("Run failed for %s", run_name)
                if run_name in self.active:
                    self.active[run_name]["status"] = "failed"
                    self.active[run_name]["ended_at"] = datetime.utcnow().isoformat()

        task = asyncio.create_task(runner())
        self.active[run_name] = {
            "agent": agent,
            "tracer": tracer,
            "targets": targets_info,
            "status": "running",
            "task": task,
            "started_at": datetime.utcnow().isoformat(),
        }
        return RunInfo(run_id=run_name, target=target, status="running", instruction=instruction)

    def list_runs(self, limit: int = 20) -> List[RunInfo]:
        self._reap_finished()
        runs: list[RunInfo] = []
        for run_id, info in list(self.active.items())[:limit]:
            runs.append(self._build_run_info(run_id, info))

        # Fill with filesystem runs not in active list
        if len(runs) < limit and self.runs_dir.exists():
            existing_ids = {r.run_id for r in runs}
            for path in sorted(self.runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if not path.is_dir():
                    continue
                if path.name in existing_ids:
                    continue
                runs.append(
                    RunInfo(
                        run_id=path.name,
                        target="unknown",
                        status="unknown",
                    )
                )
                if len(runs) >= limit:
                    break
        return runs

    def get_run_info(self, run_id: str) -> RunInfo | None:
        self._reap_finished()
        info = self.active.get(run_id)
        if not info:
            # fallback to filesystem presence
            path = self.runs_dir / run_id
            if path.exists():
                return RunInfo(run_id=run_id, target="unknown", status="unknown")
            return None
        return self._build_run_info(run_id, info)

    def tail_logs(self, run_id: str, offset: int = 0, limit: int = 200) -> List[str]:
        path = self.runs_dir / run_id
        candidates = [
            path / "stdout.log",
            path / "logs.txt",
            path / "log.txt",
            path / "run.log",
        ]
        log_file = next((p for p in candidates if p.exists()), None)
        if not log_file:
            return []
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines[offset: offset + limit]]

    def get_report_summary(self, run_id: str) -> str:
        path = self.runs_dir / run_id
        report_file = self._find_report_file(path)
        if not report_file:
            return ""
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return content[:4000]

    def get_report_file(self, run_id: str) -> str | None:
        path = self.runs_dir / run_id
        report_file = self._find_report_file(path)
        return str(report_file) if report_file else None

    def get_file_metadata(self, run_id: str, path: str) -> tuple[str, int] | None:
        base = (self.runs_dir / run_id).resolve()
        target = (base / path).resolve()
        if not str(target).startswith(str(base)) or not target.is_file():
            return None
        return str(target), target.stat().st_size

    def list_files(self, run_id: str, path: str = "") -> List[Dict[str, Any]]:
        base = (self.runs_dir / run_id / path).resolve()
        root = (self.runs_dir / run_id).resolve()
        if not str(base).startswith(str(root)) or not base.exists() or not base.is_dir():
            return []
        results: list[Dict[str, Any]] = []
        for entry in base.iterdir():
            results.append(
                {
                    "name": entry.name,
                    "path": os.path.relpath(entry, root),
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size,
                }
            )
        return results

    def read_file(self, run_id: str, path: str) -> bytes:
        base = (self.runs_dir / run_id).resolve()
        target = (base / path).resolve()
        if not str(target).startswith(str(base)) or not target.exists() or not target.is_file():
            raise FileNotFoundError("File not found")
        return target.read_bytes()

    def resume_run(self, run_id: str, stream_callback: Optional[Callable[[str, str, str, str], None]] = None) -> bool:
        self._reap_finished()
        info = self.active.get(run_id)
        if not info:
            return False
        tracer = info.get("tracer")
        if tracer and stream_callback:
            tracer.vulnerability_found_callback = stream_callback
        # If a task exists and is still running, consider it resumed
        task = info.get("task")
        if task and not task.done():
            info["status"] = "running"
            return True
        return False

    def stop_run(self, run_id: str) -> bool:
        self._reap_finished()
        info = self.active.get(run_id)
        if not info:
            return False
        agent = info.get("agent")
        if hasattr(agent, "cancel"):
            agent.cancel()
            info["status"] = "stopped"
            info["ended_at"] = datetime.utcnow().isoformat()
            return True
        task = info.get("task")
        if task:
            task.cancel()
            info["status"] = "stopped"
            info["ended_at"] = datetime.utcnow().isoformat()
            return True
        # If no cancel available, mark as stopped
        info["status"] = "stopped"
        info["ended_at"] = datetime.utcnow().isoformat()
        return True

    def _build_run_info(self, run_id: str, info: dict[str, Any]) -> RunInfo:
        target = info.get("targets", [{}])[0].get("original", "unknown")
        status = info.get("status", "running")
        ri = RunInfo(
            run_id=run_id,
            target=target,
            status=status,
        )
        return ri

    def _find_report_file(self, base: Path) -> Path | None:
        candidates = [
            base / "report.txt",
            base / "report.md",
            base / "report.html",
            base / "report.json",
            base / "report.pdf",
        ]
        for path in candidates:
            if path.exists():
                return path
        return None

    def _reap_finished(self) -> None:
        for run_id, info in self.active.items():
            task = info.get("task")
            if task and task.done():
                if task.cancelled():
                    info["status"] = "stopped"
                    info["ended_at"] = datetime.utcnow().isoformat()
                elif task.exception():
                    info["status"] = "failed"
                    info["ended_at"] = datetime.utcnow().isoformat()
                else:
                    info["status"] = "completed"
                    info["ended_at"] = datetime.utcnow().isoformat()
        # Optionally prune very old entries if needed (not implemented)
