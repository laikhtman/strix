import asyncio

import pytest

from strix.runtime.tool_pool import ToolServerPool


def make_stub():
    return object()


@pytest.mark.asyncio
async def test_tool_pool_spawns_and_reuses() -> None:
    pool = ToolServerPool(make_stub, max_instances=1)
    inst1 = await pool.get_instance()
    inst2 = await pool.get_instance()
    assert inst1 is inst2
    await pool.mark_unhealthy(inst1)
    health = await pool.get_health()
    assert health[id(inst1)] == "unhealthy"
