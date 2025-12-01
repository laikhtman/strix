from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine


class RunManager:
    def __init__(self, max_concurrent: int = 2) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_budget(
        self,
        tasks: list[tuple[str, Callable[[], Coroutine[Any, Any, Any]]]],
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}

        async def _wrap(name: str, coro_fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
            async with self.semaphore:
                try:
                    results[name] = await coro_fn()
                except Exception as exc:  # noqa: BLE001
                    results[name] = {"success": False, "error": str(exc)}

        await asyncio.gather(*[_wrap(name, fn) for name, fn in tasks])
        return results
