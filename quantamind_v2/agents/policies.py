from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantamind_v2.agents.registry import AgentRegistry


@dataclass(slots=True)
class AgentSelectionResult:
    primary_agent: str
    selected_agents: list[str]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_agent": self.primary_agent,
            "selected_agents": list(self.selected_agents),
            "reason": self.reason,
        }


class AgentPolicyEngine:
    """Resolve suitable agents based on planning signals."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def select_agents(
        self,
        *,
        route_mode: str,
        shortcut_owner: str | None,
        heuristic_owner_agents: list[str],
    ) -> AgentSelectionResult:
        resolved: list[str] = []
        if route_mode == "shortcut":
            owner = shortcut_owner or "default"
            if self.registry.has(owner):
                resolved.append(self.registry.get(owner).agent_id)  # type: ignore[union-attr]
            else:
                resolved.append("default")
            return AgentSelectionResult(
                primary_agent=resolved[0],
                selected_agents=resolved,
                reason="shortcut owner agent is preferred",
            )

        for item in heuristic_owner_agents:
            if self.registry.has(item):
                profile = self.registry.get(item)
                if profile is not None and profile.agent_id not in resolved:
                    resolved.append(profile.agent_id)
        if not resolved:
            resolved.append("default")
        if route_mode == "multi_agent_plan" and len(resolved) == 1:
            resolved.append("merger" if self.registry.has("merger") else "default")
        return AgentSelectionResult(
            primary_agent=resolved[0],
            selected_agents=resolved,
            reason="selected by heuristics and registered capability profiles",
        )
