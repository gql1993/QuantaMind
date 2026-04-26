from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentProfile:
    agent_id: str
    display_name: str
    role: str
    capabilities: list[str] = field(default_factory=list)
    default_context_layers: list[str] = field(default_factory=list)
    default_tool_classes: list[str] = field(default_factory=list)
    output_artifact_types: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "default_context_layers": list(self.default_context_layers),
            "default_tool_classes": list(self.default_tool_classes),
            "output_artifact_types": list(self.output_artifact_types),
            "aliases": list(self.aliases),
            "metadata": dict(self.metadata or {}),
        }
