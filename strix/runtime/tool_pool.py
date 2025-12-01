from __future__ import annotations

import asyncio
from typing import Any, Callable


class ToolServerPool:
    def __init__(self, spawn: Callable[[], Any], max_instances: int = 2) -> None:
        self.spawn = spawn
        self.max_instances = max_instances
        self.instances: list[Any] = []
        self.health: dict[int, str] = {}
        self.lock = asyncio.Lock()

    async def get_instance(self) -> Any:
        async with self.lock:
            for inst in self.instances:
                if self.health.get(id(inst)) == "healthy":
                    return inst

            if len(self.instances) < self.max_instances:
                inst = self.spawn()
                self.instances.append(inst)
                self.health[id(inst)] = "healthy"
                return inst

            return self.instances[0]

    async def mark_unhealthy(self, instance: Any) -> None:
        async with self.lock:
            self.health[id(instance)] = "unhealthy"

    async def get_health(self) -> dict[int, str]:
        async with self.lock:
            return dict(self.health)
