from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from litellm.types.utils import LlmProviders
from litellm.utils import ProviderConfigManager
from pydantic import ValidationError

from strix.config import openrouter_order
from strix.config.models import _install_openrouter_stream_cost_capture
from strix.config.settings import DEFAULT_OPENROUTER_COST_WEIGHTS, LlmSettings


if TYPE_CHECKING:
    from collections.abc import Iterator

    from litellm.types.llms.openai import AllMessageValues

WEIGHTS = openrouter_order.parse_weights(DEFAULT_OPENROUTER_COST_WEIGHTS)


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


def _settings(**env: str) -> LlmSettings:
    return LlmSettings.model_validate({"STRIX_LLM": "openrouter/z-ai/glm-5.3", **env})


@pytest.fixture(autouse=True)
def _clear_orders() -> Iterator[None]:
    openrouter_order._PREFERENCES.clear()
    yield
    openrouter_order._PREFERENCES.clear()


def test_ranks_by_token_mix_not_list_price() -> None:
    # Cheap output but expensive cache reads loses to the reverse for a scan.
    endpoints = [
        _endpoint("cheap-output", 1.4e-6, 1e-6, 2.6e-7),
        _endpoint("cheap-cache", 1.5e-7, 4e-6, 1.5e-7),
    ]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, set(), 95) == [
        "cheap-cache",
        "cheap-output",
    ]


def test_missing_cache_price_bills_cached_tokens_at_prompt_price() -> None:
    endpoints = [_endpoint("no-cache", 2e-7, 1e-6, None), _endpoint("cache", 3e-7, 1e-6, 1.8e-7)]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, set(), 95) == ["cache", "no-cache"]


def test_skips_unhealthy_and_excluded_endpoints() -> None:
    endpoints = [
        _endpoint("down", 1e-7, 1e-6, 1e-7, status=-2),
        _endpoint("flaky", 1e-7, 1e-6, 1e-7, uptime_last_30m=80.0),
        _endpoint("baidu/fp8", 1e-7, 1e-6, 1e-7),
        _endpoint("new", 1e-7, 1e-6, 1e-7, uptime_last_30m=None),
        _endpoint("ok", 2e-7, 1e-6, 2e-7),
    ]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, {"baidu"}, 95) == ["new", "ok"]
    assert openrouter_order.rank_endpoints(endpoints, WEIGHTS, set(), 75) == [
        "flaky",
        "baidu/fp8",
        "new",
        "ok",
    ]


@pytest.mark.parametrize("raw", ["0.9,0.1", "a,b,c", "1,-1,0"])
def test_rejects_bad_weights(raw: str) -> None:
    with pytest.raises(ValueError):
        openrouter_order.parse_weights(raw)


@pytest.mark.parametrize("raw", ['{"p95": 3}', '{"p50": 0}', "2"])
def test_rejects_bad_latency_cutoffs(raw: str) -> None:
    with pytest.raises(ValidationError):
        _settings(STRIX_OPENROUTER_MAX_LATENCY=raw)


def test_fetch_failure_leaves_routing_alone() -> None:
    with patch("strix.config.openrouter_order.httpx.get", side_effect=OSError("offline")):
        openrouter_order.configure(_settings())
    assert openrouter_order.provider_preferences("z-ai/glm-5.3") is None


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
    llm = _settings(STRIX_OPENROUTER_MAX_LATENCY='{"p50": 1.5, "p90": 4}')
    with patch("strix.config.openrouter_order.httpx.get", return_value=response) as get:
        openrouter_order.configure(llm)
        openrouter_order.configure(llm)
    get.assert_called_once()

    _install_openrouter_stream_cost_capture()
    config = ProviderConfigManager.get_provider_chat_config(
        model="z-ai/glm-5.3", provider=LlmProviders.OPENROUTER
    )
    assert config is not None
    messages: list[AllMessageValues] = [{"role": "user", "content": "hi"}]
    with patch("strix.config.models.load_settings") as settings:
        settings.return_value.llm.openrouter_sticky_sessions = False
        body = config.transform_request("z-ai/glm-5.3", messages, {}, {}, {})
        other = config.transform_request("moonshotai/kimi-k3", messages, {}, {}, {})
    assert body["provider"] == {
        "order": ["relace", "wafer"],
        "allow_fallbacks": True,
        "preferred_max_latency": {"p50": 1.5, "p90": 4.0},
    }
    assert "provider" not in other
