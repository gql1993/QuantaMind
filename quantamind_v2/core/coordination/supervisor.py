from __future__ import annotations

from typing import Dict, List

from quantamind_v2.contracts.run import RunState
from quantamind_v2.core.coordination.delegation import CoordinationDelegator
from quantamind_v2.core.coordination.merger import CoordinationMerger
from quantamind_v2.core.coordination.policies import CoordinationPolicies
from quantamind_v2.core.coordination.planner import CoordinationPlanner
from quantamind_v2.core.coordination.router import CoordinationMode, CoordinationRouter
from quantamind_v2.core.runs.coordinator import RunCoordinator


class CoordinationSupervisor:
    """Phase 1 minimal execution supervisor for coordination flows."""

    def __init__(
        self,
        coordinator: RunCoordinator,
        router: CoordinationRouter,
        planner: CoordinationPlanner,
        delegator: CoordinationDelegator,
        merger: CoordinationMerger,
        policies: CoordinationPolicies | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.router = router
        self.planner = planner
        self.delegator = delegator
        self.merger = merger
        self.policies = policies or CoordinationPolicies()

    def execute(
        self,
        run_id: str,
        message: str,
        *,
        forced_mode: CoordinationMode | None = None,
        priority: str = "normal",
        budget_seconds: float | None = None,
    ) -> Dict:
        current_run = self.coordinator.get_run(run_id)
        if current_run.state == RunState.QUEUED:
            self.coordinator.transition(
                run_id,
                RunState.RUNNING,
                stage="routing",
                status_message="Routing coordination request...",
            )
        route_result = self.router.route(message)
        if forced_mode is not None and route_result.get("mode") != forced_mode:
            route_result = {
                **route_result,
                "mode": forced_mode,
                "shortcut": None,
                "reason": f"{route_result.get('reason', '')}; forced_mode={forced_mode.value}".strip("; "),
            }
        self.policies.validate_route(route_result)
        plan = self.planner.build_plan(
            message,
            route_result,
            priority=priority,
            budget_seconds=budget_seconds,
        )
        self.policies.validate_plan(plan)

        run = self.coordinator.update_run(
            run_id,
            stage="planning",
            status_message=f"Coordination mode selected: {route_result['mode']}.",
            metadata={"route_result": {"mode": str(route_result["mode"]), "reason": route_result.get("reason", "")}, "plan": plan},
        )

        if route_result["mode"] == CoordinationMode.MULTI_AGENT_PLAN:
            delegated = self.delegator.delegate_plan(run.run_id, plan)
            child_outputs: List[Dict] = []
            for child_run in delegated["child_runs"]:
                completed = self.coordinator.transition(
                    child_run.run_id,
                    RunState.RUNNING,
                    stage="child_running",
                    status_message=f"Running delegated child run for {child_run.owner_agent or 'unknown'}",
                )
                completed = self.coordinator.update_run(
                    completed.run_id,
                    stage="child_completed",
                    status_message=f"Delegated child run completed for {completed.owner_agent or 'unknown'}",
                    metadata={
                        "summary": f"{completed.owner_agent or 'unknown'} completed delegated step.",
                    },
                )
                completed = self.coordinator.transition(
                    completed.run_id,
                    RunState.COMPLETED,
                    stage=completed.stage,
                    status_message=completed.status_message,
                )
                child_outputs.append(
                    {
                        "run_id": completed.run_id,
                        "owner_agent": completed.owner_agent,
                        "status_message": completed.status_message,
                        "summary": completed.metadata.get("summary", ""),
                    }
                )
            merged = self.merger.merge(child_outputs)
            run = self.coordinator.update_run(
                run.run_id,
                stage="merged",
                status_message=merged["summary"] or "Multi-agent plan completed.",
                metadata={"merged_result": merged},
            )
            run = self.coordinator.transition(
                run.run_id,
                RunState.COMPLETED,
                stage=run.stage,
                status_message=run.status_message,
            )
            return {
                "run": run,
                "plan": plan,
                "route_result": route_result,
                "delegated": delegated,
                "merged": merged,
            }

        run = self.coordinator.update_run(
            run.run_id,
            stage="planned",
            status_message=f"Plan ready for mode: {route_result['mode']}.",
        )
        run = self.coordinator.transition(
            run.run_id,
            RunState.COMPLETED,
            stage=run.stage,
            status_message=run.status_message,
        )
        return {"run": run, "plan": plan, "route_result": route_result}
