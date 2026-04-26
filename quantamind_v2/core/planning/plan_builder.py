from __future__ import annotations

from typing import Any

from quantamind_v2.agents import AgentPolicyEngine, AgentRegistry, build_default_agent_registry
from quantamind_v2.core.coordination.router import CoordinationMode
from quantamind_v2.core.planning.heuristics import evaluate_message_heuristics
from quantamind_v2.core.planning.intent import detect_intent


class PlanBuilder:
    """Build normalized plans enriched with intent + heuristic metadata."""

    def __init__(self, agent_registry: AgentRegistry | None = None) -> None:
        self.agent_registry = agent_registry or build_default_agent_registry()
        self.agent_policy = AgentPolicyEngine(self.agent_registry)

    def build(
        self,
        message: str,
        route_result: dict[str, Any],
        *,
        priority: str = "normal",
        budget_seconds: float | None = None,
    ) -> dict[str, Any]:
        mode = route_result["mode"]
        intent = detect_intent(message)
        heuristics = evaluate_message_heuristics(
            message,
            priority=priority,
            budget_seconds=budget_seconds,
        )
        route_mode_value = getattr(mode, "value", str(mode))
        shortcut_owner = None
        if route_result.get("shortcut") is not None:
            shortcut_owner = route_result["shortcut"].owner_agent
        agent_selection = self.agent_policy.select_agents(
            route_mode=route_mode_value,
            shortcut_owner=shortcut_owner,
            heuristic_owner_agents=list(heuristics.owner_agents),
        )
        scheduling = {
            "requested_priority": heuristics.requested_priority,
            "priority": heuristics.effective_priority,
            "budget_seconds": heuristics.budget_seconds,
            "budget_risk": heuristics.budget_risk,
            "queue_hint": "expedite" if heuristics.effective_priority == "high" else "standard",
            "strategy": "parallel" if mode == CoordinationMode.MULTI_AGENT_PLAN else "single_path",
        }
        if mode == CoordinationMode.SHORTCUT:
            shortcut = route_result["shortcut"]
            return {
                "mode": mode,
                "title": f"shortcut:{shortcut.name}",
                "steps": [
                    {
                        "kind": "shortcut",
                        "name": shortcut.name,
                        "owner_agent": agent_selection.primary_agent,
                        "description": shortcut.description,
                    }
                ],
                "intent": {
                    "name": intent.intent.value,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                },
                "heuristics": heuristics.to_dict(),
                "agent_selection": agent_selection.to_dict(),
                "scheduling": scheduling,
            }

        if mode == CoordinationMode.MULTI_AGENT_PLAN:
            owner_agents = list(agent_selection.selected_agents)
            if len(owner_agents) < 2:
                owner_agents = ["planner", "merger"]
            return {
                "mode": mode,
                "title": "multi_agent_plan",
                "steps": [
                    {
                        "kind": "delegate",
                        "name": "specialist_analysis",
                        "owner_agent": owner_agents[0],
                        "description": "Split the task into specialist runs and collect outputs.",
                    },
                    {
                        "kind": "merge",
                        "name": "merge_results",
                        "owner_agent": owner_agents[1] if len(owner_agents) > 1 else "merger",
                        "description": "Merge specialist outputs into one final result.",
                    },
                ],
                "intent": {
                    "name": intent.intent.value,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                },
                "heuristics": heuristics.to_dict(),
                "agent_selection": agent_selection.to_dict(),
                "scheduling": scheduling,
            }

        return {
            "mode": mode,
            "title": "single_agent_plan",
            "steps": [
                {
                    "kind": "single_agent",
                    "name": "single_agent_response",
                    "owner_agent": agent_selection.primary_agent,
                    "description": "Handle the request with one primary agent.",
                }
            ],
            "intent": {
                "name": intent.intent.value,
                "confidence": intent.confidence,
                "reason": intent.reason,
            },
            "heuristics": heuristics.to_dict(),
            "agent_selection": agent_selection.to_dict(),
            "scheduling": scheduling,
        }
