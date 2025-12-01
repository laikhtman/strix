import sqlite3
from pathlib import Path
from typing import Optional


class BotState:
    """
    Lightweight SQLite-backed state for run preferences (e.g., verbosity).
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_settings (
                    run_id TEXT PRIMARY KEY,
                    verbosity TEXT
                )
                """
            )
            conn.commit()

    def set_verbosity(self, run_id: str, verbosity: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO run_settings (run_id, verbosity)
                VALUES (?, ?)
                ON CONFLICT(run_id) DO UPDATE SET verbosity=excluded.verbosity
                """,
                (run_id, verbosity),
            )
            conn.commit()

    def get_verbosity(self, run_id: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT verbosity FROM run_settings WHERE run_id = ?", (run_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None
