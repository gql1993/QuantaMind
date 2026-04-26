from __future__ import annotations

from typing import Dict

from quantamind_v2.core.coordination.router import CoordinationMode


class CoordinationPolicies:
    """Phase 1 minimal policy checks for coordination execution."""

    _MAX_PLAN_STEPS = 8

    def validate_route(self, route_result: Dict) -> None:
        mode = route_result.get("mode")
        if mode not in {
            CoordinationMode.SINGLE_AGENT,
            CoordinationMode.SHORTCUT,
            CoordinationMode.MULTI_AGENT_PLAN,
        }:
            raise ValueError(f"unsupported coordination mode: {mode}")

    def validate_plan(self, plan: Dict) -> None:
        steps = plan.get("steps", [])
        if not steps:
            raise ValueError("coordination plan must contain at least one step")
        if len(steps) > self._MAX_PLAN_STEPS:
            raise ValueError(f"coordination plan exceeds max steps: {len(steps)}")
        for step in steps:
            if not step.get("kind"):
                raise ValueError("coordination step missing `kind`")
            if not step.get("name"):
                raise ValueError("coordination step missing `name`")
            if not step.get("owner_agent"):
                raise ValueError("coordination step missing `owner_agent`")
