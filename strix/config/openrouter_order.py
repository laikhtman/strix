"""Rank a model's OpenRouter providers by what a Strix scan actually pays.

OpenRouter's ``sort: "price"`` ranks providers by list price, and output
price dominates it. A scan's tokens are almost all cached input, so the
cheapest provider by list price is often not the cheapest one to run.
This module fetches the model's endpoints once at startup, scores each by
its cached-input, uncached-input, and output prices weighted by a scan's
token mix, and hands OpenRouter the ranking as an explicit provider order.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)

ENDPOINTS_URL = "https://openrouter.ai/api/v1/models/{model}/endpoints"
# Endpoints that were down for more than this share of the last 30 minutes
# are left out of the order (OpenRouter can still fall back to them).
MIN_UPTIME_PERCENT = 95.0
FETCH_TIMEOUT_S = 5.0

# Default shares of a scan's tokens that are cached input, uncached input, and
# output, measured on GLM-5.3 scans with a ~97% cache hit rate.
DEFAULT_WEIGHTS = "0.97,0.0277,0.0023"

# OpenRouter model id (no "openrouter/" prefix) -> ranked endpoint tags.
_ORDERS: dict[str, list[str]] = {}


def parse_weights(raw: str) -> tuple[float, float, float]:
    """Parse ``"cached,uncached,output"`` token-share weights."""
    parts = [float(part) for part in raw.split(",")]
    if len(parts) != 3 or any(part < 0 for part in parts):
        raise ValueError(f"expected three non-negative weights, got {raw!r}")
    return parts[0], parts[1], parts[2]


def effective_price(pricing: dict[str, Any], weights: tuple[float, float, float]) -> float:
    """Per-token price of an endpoint under the given token mix."""
    prompt = float(pricing.get("prompt") or 0)
    completion = float(pricing.get("completion") or 0)
    # An endpoint without a cache-read price bills cached tokens at full price.
    cache_read = pricing.get("input_cache_read")
    cached = float(cache_read) if cache_read is not None else prompt
    w_cached, w_uncached, w_output = weights
    return w_cached * cached + w_uncached * prompt + w_output * completion


def rank_endpoints(
    endpoints: list[dict[str, Any]],
    weights: tuple[float, float, float],
    exclude: set[str],
) -> list[str]:
    """Endpoint tags from cheapest to most expensive, skipping unhealthy ones."""
    scored: list[tuple[float, str]] = []
    for endpoint in endpoints:
        tag = endpoint.get("tag")
        name = str(endpoint.get("provider_name") or "").lower()
        if not tag or tag.lower() in exclude or name in exclude:
            continue
        if (endpoint.get("status") or 0) < 0:
            continue
        uptime = endpoint.get("uptime_last_30m")
        if uptime is not None and uptime < MIN_UPTIME_PERCENT:
            continue
        scored.append((effective_price(endpoint.get("pricing") or {}, weights), tag))
    scored.sort(key=lambda item: item[0])
    return [tag for _, tag in scored]


def configure(model_name: str, weights_raw: str, exclude_raw: str) -> None:
    """Fetch and rank the model's endpoints once; failures leave routing alone."""
    model = model_name.strip().removeprefix("openrouter/")
    if model in _ORDERS:
        return
    try:
        weights = parse_weights(weights_raw)
        response = httpx.get(ENDPOINTS_URL.format(model=model), timeout=FETCH_TIMEOUT_S)
        response.raise_for_status()
        endpoints = response.json()["data"]["endpoints"]
    except Exception as exc:  # noqa: BLE001 - routing falls back to OpenRouter's default
        logger.warning("OpenRouter cost order disabled for %s: %s", model, exc)
        return
    exclude = {item.strip().lower() for item in exclude_raw.split(",") if item.strip()}
    order = rank_endpoints(endpoints, weights, exclude)
    if order:
        _ORDERS[model] = order
        logger.info("OpenRouter cost order for %s: %s", model, ", ".join(order))


def provider_preferences(model: str, max_latency_p50: float | None) -> dict[str, Any] | None:
    """The request's ``provider`` object, or None when no order is known."""
    order = _ORDERS.get(model)
    if not order:
        return None
    preferences: dict[str, Any] = {"order": order, "allow_fallbacks": True}
    if max_latency_p50 is not None:
        preferences["preferred_max_latency"] = {"p50": max_latency_p50}
    return preferences
