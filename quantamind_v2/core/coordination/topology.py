from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class CoordinationNode(BaseModel):
    node_id: str
    kind: str
    name: str
    owner_agent: str
    description: str = ""
    run_id: str | None = None
    depends_on: List[str] = Field(default_factory=list)


class CoordinationTopology(BaseModel):
    root_run_id: str
    nodes: List[CoordinationNode] = Field(default_factory=list)

    def as_dependency_map(self) -> Dict[str, List[str]]:
        return {node.node_id: list(node.depends_on) for node in self.nodes}
