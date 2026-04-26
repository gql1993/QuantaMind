from __future__ import annotations

from quantamind_v2.agents.base import AgentProfile


class AgentRegistry:
    """In-memory registry for agent capability profiles."""

    def __init__(self) -> None:
        self._items: dict[str, AgentProfile] = {}
        self._alias_to_id: dict[str, str] = {}

    def register(self, profile: AgentProfile, *, replace: bool = False) -> None:
        agent_id = profile.agent_id.strip().lower()
        if not agent_id:
            raise ValueError("agent_id cannot be empty")
        if agent_id in self._items and not replace:
            raise ValueError(f"agent profile already exists: {agent_id}")
        normalized = AgentProfile(
            agent_id=agent_id,
            display_name=profile.display_name,
            role=profile.role,
            capabilities=list(profile.capabilities),
            default_context_layers=list(profile.default_context_layers),
            default_tool_classes=list(profile.default_tool_classes),
            output_artifact_types=list(profile.output_artifact_types),
            aliases=list(profile.aliases),
            metadata=dict(profile.metadata or {}),
        )
        self._items[agent_id] = normalized
        self._alias_to_id[agent_id] = agent_id
        for alias in normalized.aliases:
            self._alias_to_id[alias.strip().lower()] = agent_id

    def get(self, agent_id_or_alias: str) -> AgentProfile | None:
        key = agent_id_or_alias.strip().lower()
        resolved = self._alias_to_id.get(key, key)
        return self._items.get(resolved)

    def list(self) -> list[AgentProfile]:
        return list(self._items.values())

    def has(self, agent_id_or_alias: str) -> bool:
        return self.get(agent_id_or_alias) is not None


def build_default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    profiles = [
        AgentProfile(
            agent_id="default",
            display_name="Default Agent",
            role="fallback assistant",
            capabilities=["general_response"],
            default_context_layers=["system", "recent_conversation"],
            default_tool_classes=["query"],
            output_artifact_types=["generic_artifact"],
            aliases=["assistant"],
        ),
        AgentProfile(
            agent_id="planner",
            display_name="Planning Coordinator",
            role="builds and supervises multi-step plans",
            capabilities=["planning", "delegation"],
            default_context_layers=["system", "policy", "project_memory"],
            default_tool_classes=["query", "long_running"],
            output_artifact_types=["coordination_report"],
            aliases=["coordinator"],
        ),
        AgentProfile(
            agent_id="merger",
            display_name="Result Merger",
            role="merges specialist outputs into final report",
            capabilities=["merge", "summarization"],
            default_context_layers=["system", "artifact"],
            default_tool_classes=["query"],
            output_artifact_types=["coordination_report"],
        ),
        AgentProfile(
            agent_id="system",
            display_name="System Operator",
            role="checks gateway/system runtime state",
            capabilities=["system_status", "diagnosis"],
            default_context_layers=["system", "data_snapshot"],
            default_tool_classes=["query"],
            output_artifact_types=["system_diagnosis", "db_health_report"],
        ),
        AgentProfile(
            agent_id="intel_officer",
            display_name="Intel Officer",
            role="generates daily intel and summaries",
            capabilities=["intel_digest", "reporting"],
            default_context_layers=["system", "project_memory", "artifact"],
            default_tool_classes=["query", "long_running"],
            output_artifact_types=["intel_report"],
            aliases=["intel"],
        ),
        AgentProfile(
            agent_id="data_analyst",
            display_name="Data Analyst",
            role="analyzes metrics and data health",
            capabilities=["data_analysis", "database_health"],
            default_context_layers=["system", "data_snapshot", "artifact"],
            default_tool_classes=["query", "mutation"],
            output_artifact_types=["db_health_report", "pipeline_report"],
            aliases=["db_analyst"],
        ),
        AgentProfile(
            agent_id="design_specialist",
            display_name="Design Specialist",
            role="handles design related analysis",
            capabilities=["design_analysis"],
            default_context_layers=["system", "project_memory"],
            default_tool_classes=["query", "long_running"],
            output_artifact_types=["coordination_report"],
        ),
        AgentProfile(
            agent_id="process_engineer",
            display_name="Process Engineer",
            role="handles process and release risk analysis",
            capabilities=["process_analysis", "release_risk"],
            default_context_layers=["system", "project_memory", "data_snapshot"],
            default_tool_classes=["query", "long_running"],
            output_artifact_types=["coordination_report", "pipeline_report"],
        ),
        AgentProfile(
            agent_id="simulation_specialist",
            display_name="Simulation Specialist",
            role="handles simulation and experiment analysis",
            capabilities=["simulation_analysis"],
            default_context_layers=["system", "project_memory", "artifact"],
            default_tool_classes=["long_running"],
            output_artifact_types=["simulation_report", "coordination_report"],
            aliases=["sim_specialist"],
        ),
    ]
    for profile in profiles:
        registry.register(profile)
    return registry
