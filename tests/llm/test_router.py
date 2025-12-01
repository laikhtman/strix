import asyncio

import pytest

from strix.llm.router import MultiplexingLLM


class DummyLLM:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls = 0

    async def generate(self, *args, **kwargs):  # type: ignore[override]
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("failure")
        return "ok"


@pytest.mark.asyncio
async def test_multiplexing_llm_fallbacks() -> None:
    primary = DummyLLM(should_fail=True)
    fallback = DummyLLM()
    router = MultiplexingLLM(primary, fallback)

    result = await router.generate("msg")

    assert result == "ok"
    assert primary.calls == 1
    assert fallback.calls == 1


@pytest.mark.asyncio
async def test_multiplexing_llm_raises_without_fallback() -> None:
    primary = DummyLLM(should_fail=True)
    router = MultiplexingLLM(primary, None)

    with pytest.raises(RuntimeError):
        await router.generate("msg")
