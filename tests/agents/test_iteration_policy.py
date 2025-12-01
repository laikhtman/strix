from strix.agents.iteration_policy import calculate_iteration_budget


def test_calculate_iteration_budget_scales_with_targets() -> None:
    targets = [
        {"type": "repository", "details": {}},
        {"type": "web_application", "details": {}},
        {"type": "local_code", "details": {}},
    ]

    result = calculate_iteration_budget(targets, llm_timeout=700, base=300)

    assert result["max_iterations"] >= 300
    assert result["inputs"]["target_weight"] == 5
    assert result["inputs"]["latency_adjustment"] > 0


def test_calculate_iteration_budget_bounds() -> None:
    result = calculate_iteration_budget([], llm_timeout=None, base=50)
    assert result["max_iterations"] >= 180

    result = calculate_iteration_budget([{"type": "repository"}] * 20, llm_timeout=2000, base=500)
    assert result["max_iterations"] <= 600
