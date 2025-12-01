from __future__ import annotations

from typing import Any

DEFAULT_BASE = 300
MIN_CAP = 180
MAX_CAP = 600


def calculate_iteration_budget(
    targets: list[dict[str, Any]] | None,
    llm_timeout: int | None,
    base: int = DEFAULT_BASE,
) -> dict[str, Any]:
    targets = targets or []
    target_count = len(targets)

    weight = 0
    for target in targets:
        target_type = target.get("type", "")
        if target_type in {"repository", "web_application"}:
            weight += 2
        elif target_type in {"local_code", "ip_address"}:
            weight += 1

    latency_adj = 0
    if llm_timeout:
        if llm_timeout > 900:
            latency_adj = 60
        elif llm_timeout > 600:
            latency_adj = 40
        elif llm_timeout > 300:
            latency_adj = 20

    budget = base + (weight * 20) + latency_adj
    budget = max(MIN_CAP, min(MAX_CAP, budget))

    return {
        "max_iterations": budget,
        "inputs": {
            "target_count": target_count,
            "target_weight": weight,
            "llm_timeout": llm_timeout,
            "base": base,
            "latency_adjustment": latency_adj,
        },
        "rationale": (
            "Scaled iterations based on target mix and LLM timeout; "
            f"clamped to [{MIN_CAP}, {MAX_CAP}]"
        ),
    }
