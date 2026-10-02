"""Rank a model's OpenRouter providers by what a Strix scan actually pays.

OpenRouter's ``sort: "price"`` is dominated by output price, but a scan's
tokens are mostly cached input. This scores each endpoint by a scan's token
mix and sends the ranking as an explicit provider ``order``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx


if TYPE_CHECKING:
    from strix.config.settings import LlmSettings


logger = logging.getLogger(__name__)

ENDPOINTS_URL = "https://openrouter.ai/api/v1/models/{model}/endpoints"

_PREFERENCES: dict[str, dict[str, Any]] = {}


def parse_weights(raw: str) -> tuple[float, float, float]:
    cached, uncached, output = (float(part) for part in raw.split(","))
    if min(cached, uncached, output) < 0:
        raise ValueError(f"weights must be non-negative, got {raw!r}")
    return cached, uncached, output


def effective_price(pricing: dict[str, Any], weights: tuple[float, float, float]) -> float:
    prompt = float(pricing.get("prompt") or 0)
    cached = float(pricing.get("input_cache_read") or prompt)
    output = float(pricing.get("completion") or 0)
    return weights[0] * cached + weights[1] * prompt + weights[2] * output


def _usable(endpoint: dict[str, Any], exclude: set[str], min_uptime: float) -> bool:
    names = {str(endpoint.get(key) or "").lower() for key in ("tag", "provider_name")}
    uptime = endpoint.get("uptime_last_30m")
    return (
        bool(endpoint.get("tag"))
        and not names & exclude
        and (endpoint.get("status") or 0) >= 0
        and (uptime is None or uptime >= min_uptime)
    )


def rank_endpoints(
    endpoints: list[dict[str, Any]],
    weights: tuple[float, float, float],
    exclude: set[str],
    min_uptime: float,
) -> list[str]:
    usable = [endpoint for endpoint in endpoints if _usable(endpoint, exclude, min_uptime)]
    usable.sort(key=lambda endpoint: effective_price(endpoint.get("pricing") or {}, weights))
    return [endpoint["tag"] for endpoint in usable]


def configure(llm: LlmSettings) -> None:
    """Rank the model's endpoints once; on any failure, routing is left to OpenRouter."""
    model = (llm.model or "").strip().removeprefix("openrouter/")
    if model in _PREFERENCES:
        return
    try:
        response = httpx.get(ENDPOINTS_URL.format(model=model), timeout=5)
        response.raise_for_status()
        order = rank_endpoints(
            response.json()["data"]["endpoints"],
            parse_weights(llm.openrouter_cost_weights),
            {
                item.strip().lower()
                for item in llm.openrouter_order_exclude.split(",")
                if item.strip()
            },
            llm.openrouter_min_uptime,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenRouter cost order disabled for %s: %s", model, exc)
        return
    if not order:
        return
    preferences: dict[str, Any] = {"order": order, "allow_fallbacks": True}
    if llm.openrouter_max_latency:
        preferences["preferred_max_latency"] = llm.openrouter_max_latency
    _PREFERENCES[model] = preferences
    logger.info("OpenRouter cost order for %s: %s", model, ", ".join(order))


def provider_preferences(model: str) -> dict[str, Any] | None:
    return _PREFERENCES.get(model)
