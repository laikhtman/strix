import json
from pathlib import Path

import pytest

from strix.agents.graph_builder import (
    AgentGraphSpec,
    GraphBuilderError,
    load_graph_spec,
    parse_graph_spec,
)


def test_parse_graph_spec_validates_and_returns_root() -> None:
    raw = {
        "agents": [
            {"id": "root", "name": "Root", "task": "Root task"},
            {"id": "child", "name": "Child", "task": "Child task", "parent_id": "root"},
        ]
    }

    spec = parse_graph_spec(raw)

    assert isinstance(spec, AgentGraphSpec)
    assert spec.root.id == "root"
    graph_dict = spec.as_graph_dict()
    assert len(graph_dict["nodes"]) == 2
    assert graph_dict["edges"] == [{"from": "root", "to": "child", "type": "delegation"}]


def test_parse_graph_spec_rejects_invalid_parent() -> None:
    raw = {"agents": [{"id": "orphan", "name": "Orphan", "task": "Task", "parent_id": "missing"}]}
    with pytest.raises(GraphBuilderError):
        parse_graph_spec(raw)


def test_load_graph_spec_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "agents": [
                    {
                        "id": "root",
                        "name": "Root",
                        "task": "Root task",
                        "prompt_modules": ["root_agent"],
                        "max_iterations": 123,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    spec = load_graph_spec(path)
    configs = spec.build_agent_configs({"llm_prompt_modules": ["default"]})

    assert configs[0]["agent_id"] == "root"
    assert configs[0]["max_iterations"] == 123
    assert configs[0]["llm_prompt_modules"] == ["root_agent"]
