from __future__ import annotations

from typing import Dict

from quantamind_v2.core.coordination.router import CoordinationMode
from quantamind_v2.core.planning import PlanBuilder


class CoordinationPlanner:
    """Phase 1 minimal planner that returns a simple plan structure."""

    def __init__(self, plan_builder: PlanBuilder | None = None) -> None:
        self.plan_builder = plan_builder or PlanBuilder()

    def build_plan(
        self,
        message: str,
        route_result: Dict,
        *,
        priority: str = "normal",
        budget_seconds: float | None = None,
    ) -> Dict:
        plan = self.plan_builder.build(
            message,
            route_result,
            priority=priority,
            budget_seconds=budget_seconds,
        )
        mode = plan["mode"]
        # Keep legacy behavior stable for existing callers/tests.
        if mode in {CoordinationMode.SHORTCUT, CoordinationMode.MULTI_AGENT_PLAN, CoordinationMode.SINGLE_AGENT}:
            return plan
        return {
            "mode": CoordinationMode.SINGLE_AGENT,
            "title": "single_agent_plan",
            "steps": [
                {
                    "kind": "single_agent",
                    "name": "single_agent_response",
                    "owner_agent": "default",
                    "description": "Handle the request with one primary agent.",
                }
            ],
            "intent": plan.get("intent", {}),
            "heuristics": plan.get("heuristics", {}),
        }
