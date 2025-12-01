from pathlib import Path

from strix.agents.state import AgentState


def test_state_save_and_load_round_trip(tmp_path: Path) -> None:
    state = AgentState(agent_name="Tester", task="Do work", iteration=5)
    state.add_message("user", "hello")
    path = tmp_path / "state.json"

    saved_path = state.save_to_path(path)
    loaded = AgentState.load_from_path(saved_path)

    assert loaded.agent_name == "Tester"
    assert loaded.task == "Do work"
    assert loaded.messages[-1]["content"] == "hello"
    assert loaded.iteration == 5
