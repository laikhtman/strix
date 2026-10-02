from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from litellm.types.utils import LlmProviders
from litellm.utils import ProviderConfigManager

from strix.config import openrouter_order
from strix.config.models import _install_openrouter_stream_cost_capture
from strix.config.openrouter_order import DEFAULT_WEIGHTS


if TYPE_CHECKING:
    from collections.abc import Iterator

    from litellm.types.llms.openai import AllMessageValues

WEIGHTS = openrouter_order.parse_weights(DEFAULT_WEIGHTS)


def _endpoint(
    tag: str, prompt: float, completion: float, cache_read: float | None, **extra: Any
) -> dict[str, Any]:
    pricing: dict[str, Any] = {"prompt": str(prompt), "completion": str(completion)}
    if cache_read is not None:
        pricing["input_cache_read"] = str(cache_read)
    return {
        "tag": tag,
        "provider_name": tag.split("/", maxsplit=1)[0].title(),
        "status": 0,
        "uptime_last_30m": 100,
        "pricing": pricing,
        **extra,
    }


@pytest.fixture(autouse=True)
def _clear_orders() -> Iterator[None]:
    openrouter_order._ORDERS.clear()
    yield
    openrouter_order._ORDERS.clear()


def test_ranks_by_token_mix_not_list_price() -> None:
    # Cheap output but expensive cache reads loses to the reverse for a scan.
    endpoints = [
        _endpoint("cheap-output", 1.4e-6, 1e-6, 2.6e-7),
        _endpoint("cheap-cache", 1.5e-7, 4e-6, 1.5e-7),
    ]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, set()) == [
        "cheap-cache",
        "cheap-output",
    ]


def test_missing_cache_price_bills_cached_tokens_at_prompt_price() -> None:
    endpoints = [_endpoint("no-cache", 2e-7, 1e-6, None), _endpoint("cache", 3e-7, 1e-6, 1.8e-7)]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, set()) == ["cache", "no-cache"]


def test_skips_unhealthy_and_excluded_endpoints() -> None:
    endpoints = [
        _endpoint("down", 1e-7, 1e-6, 1e-7, status=-2),
        _endpoint("flaky", 1e-7, 1e-6, 1e-7, uptime_last_30m=80.0),
        _endpoint("baidu/fp8", 1e-7, 1e-6, 1e-7),
        _endpoint("new", 1e-7, 1e-6, 1e-7, uptime_last_30m=None),
        _endpoint("ok", 2e-7, 1e-6, 2e-7),
    ]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, {"baidu"}) == ["new", "ok"]


@pytest.mark.parametrize("raw", ["0.9,0.1", "a,b,c", "1,-1,0"])
def test_rejects_bad_weights(raw: str) -> None:
    with pytest.raises(ValueError):
        openrouter_order.parse_weights(raw)


def test_fetch_failure_leaves_routing_alone() -> None:
    with patch("strix.config.openrouter_order.httpx.get", side_effect=OSError("offline")):
        openrouter_order.configure("openrouter/z-ai/glm-5.3", DEFAULT_WEIGHTS, "")
    assert openrouter_order.provider_preferences("z-ai/glm-5.3", None) is None


def test_request_carries_cost_order_and_latency_preference() -> None:
    response = MagicMock()
    response.json.return_value = {
        "data": {
            "endpoints": [
                _endpoint("wafer", 2.2e-7, 3.4e-6, 1.8e-7),
                _endpoint("relace", 1.5e-7, 4e-6, 1.5e-7),
            ]
        }
    }
    with patch("strix.config.openrouter_order.httpx.get", return_value=response) as get:
        openrouter_order.configure("openrouter/z-ai/glm-5.3", DEFAULT_WEIGHTS, "")
        openrouter_order.configure("openrouter/z-ai/glm-5.3", DEFAULT_WEIGHTS, "")
    get.assert_called_once()

    _install_openrouter_stream_cost_capture()
    config = ProviderConfigManager.get_provider_chat_config(
        model="z-ai/glm-5.3", provider=LlmProviders.OPENROUTER
    )
    assert config is not None
    messages: list[AllMessageValues] = [{"role": "user", "content": "hi"}]
    with patch("strix.config.models.load_settings") as settings:
        settings.return_value.llm.openrouter_sticky_sessions = False
        settings.return_value.llm.openrouter_max_latency_p50 = 1.5
        body = config.transform_request("z-ai/glm-5.3", messages, {}, {}, {})
        other = config.transform_request("moonshotai/kimi-k3", messages, {}, {}, {})
    assert body["provider"] == {
        "order": ["relace", "wafer"],
        "allow_fallbacks": True,
        "preferred_max_latency": {"p50": 1.5},
    }
    assert "provider" not in other
