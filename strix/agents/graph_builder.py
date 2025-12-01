from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, model_validator


class GraphBuilderError(ValueError):
    """Raised when an agent graph definition cannot be parsed or validated."""


class AgentNodeSpec(BaseModel):
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Display name for the agent")
    task: str = Field(..., description="Task or objective for the agent")
    parent_id: str | None = Field(
        default=None, description="Parent agent id; root agents omit this."
    )
    prompt_modules: list[str] = Field(default_factory=list)
    max_iterations: int | None = Field(
        default=None, description="Optional per-agent iteration cap override"
    )


class AgentGraphSpec(BaseModel):
    agents: list[AgentNodeSpec]

    @model_validator(mode="after")
    def _validate_graph(self) -> "AgentGraphSpec":
        if not self.agents:
            raise ValueError("At least one agent must be defined")

        ids = {agent.id for agent in self.agents}
        if len(ids) != len(self.agents):
            raise ValueError("Agent ids must be unique")

        roots = [agent for agent in self.agents if agent.parent_id is None]
        if len(roots) != 1:
            raise ValueError("Exactly one root agent (parent_id omitted) is required")

        for agent in self.agents:
            if agent.parent_id and agent.parent_id not in ids:
                raise ValueError(f"Agent '{agent.id}' references unknown parent '{agent.parent_id}'")

        return self

    @property
    def root(self) -> AgentNodeSpec:
        for agent in self.agents:
            if agent.parent_id is None:
                return agent
        raise GraphBuilderError("Root agent not found after validation")

    def as_graph_dict(self) -> dict[str, Any]:
        nodes = []
        edges = []

        for agent in self.agents:
            nodes.append(
                {
                    "id": agent.id,
                    "name": agent.name,
                    "task": agent.task,
                    "parent_id": agent.parent_id,
                    "prompt_modules": agent.prompt_modules,
                    "max_iterations": agent.max_iterations,
                    "status": "planned",
                }
            )
            if agent.parent_id:
                edges.append({"from": agent.parent_id, "to": agent.id, "type": "delegation"})

        return {"nodes": nodes, "edges": edges}

    def build_agent_configs(self, base_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        base_config = base_config.copy() if base_config else {}

        configs: list[dict[str, Any]] = []
        for agent in self.agents:
            cfg = base_config.copy()
            cfg["agent_id"] = agent.id
            cfg["agent_name"] = agent.name
            if agent.max_iterations is not None:
                cfg["max_iterations"] = agent.max_iterations
            if agent.prompt_modules:
                cfg["llm_prompt_modules"] = agent.prompt_modules
            cfg["parent_id"] = agent.parent_id
            cfg["task"] = agent.task
            configs.append(cfg)
        return configs


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise GraphBuilderError(
            "PyYAML is required to load YAML agent graph definitions. "
            "Install with `pip install pyyaml` or supply JSON."
        ) from exc

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_graph_spec(path: str | Path) -> AgentGraphSpec:
    path_obj = Path(path)
    if not path_obj.exists():
        raise GraphBuilderError(f"Graph file not found: {path_obj}")

    suffix = path_obj.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        raw = _load_yaml(path_obj)
    else:
        raw = json.loads(path_obj.read_text(encoding="utf-8"))

    return parse_graph_spec(raw)


def parse_graph_spec(raw: dict[str, Any]) -> AgentGraphSpec:
    if "agents" not in raw:
        raise GraphBuilderError("Graph definition must contain an 'agents' list")

    try:
        return AgentGraphSpec(**raw)
    except ValidationError as exc:  # pragma: no cover - pydantic provides details
        raise GraphBuilderError(str(exc)) from exc
