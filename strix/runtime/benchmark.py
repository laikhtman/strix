from __future__ import annotations

import time
from typing import Any, Callable


def run_benchmark(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    start = time.perf_counter()
    result = fn()
    duration_ms = (time.perf_counter() - start) * 1000
    return {"name": name, "duration_ms": round(duration_ms, 2), "result": result}
