from __future__ import annotations

from typing import Any, Callable, Protocol


class ChatBackend(Protocol):
    def generate(self, *args: Any, **kwargs: Any) -> Any: ...


class MultiplexingLLM:
    def __init__(
        self,
        primary: ChatBackend,
        fallback: ChatBackend | None = None,
        should_retry: Callable[[Exception], bool] | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.should_retry = should_retry or (lambda exc: True)

    async def generate(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return await self.primary.generate(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            if self.fallback and self.should_retry(exc):
                return await self.fallback.generate(*args, **kwargs)
            raise
