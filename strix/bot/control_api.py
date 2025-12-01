from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable


@dataclass
class RunInfo:
    run_id: str
    target: str
    status: str
    severity_summary: Optional[Dict[str, int]] = None
    started_at: Optional[str] = None
    instruction: Optional[str] = None


class ControlAPI:
    """
    Thin abstraction for bot handlers to interact with Strix without spawning CLI.
    Implementations should wire into existing Strix internals.
    """

    def start_run(
        self,
        target: str,
        instruction: str | None = None,
        verbosity: str | None = None,
        stream_callback: Optional[Callable[[str, str, str, str], None]] = None,
    ) -> RunInfo:
        raise NotImplementedError

    def list_runs(self, limit: int = 20) -> List[RunInfo]:
        raise NotImplementedError

    def get_run_info(self, run_id: str) -> RunInfo | None:
        raise NotImplementedError

    def tail_logs(self, run_id: str, offset: int = 0, limit: int = 200) -> List[str]:
        raise NotImplementedError

    def get_report_summary(self, run_id: str) -> str:
        raise NotImplementedError

    def get_report_file(self, run_id: str) -> str | None:
        raise NotImplementedError

    def get_file_metadata(self, run_id: str, path: str) -> tuple[str, int] | None:
        raise NotImplementedError

    def list_files(self, run_id: str, path: str = "") -> List[Dict[str, Any]]:
        raise NotImplementedError

    def read_file(self, run_id: str, path: str) -> bytes:
        raise NotImplementedError

    def resume_run(self, run_id: str, stream_callback: Optional[Callable[[str, str, str, str], None]] = None) -> bool:
        raise NotImplementedError

    def stop_run(self, run_id: str) -> bool:
        raise NotImplementedError
