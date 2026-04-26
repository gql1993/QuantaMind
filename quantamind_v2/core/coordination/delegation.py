from __future__ import annotations

from typing import Dict, List

from quantamind_v2.contracts.run import RunRecord, RunType
from quantamind_v2.core.coordination.topology import CoordinationNode, CoordinationTopology
from quantamind_v2.core.runs.coordinator import RunCoordinator


class CoordinationDelegator:
    """Phase 1 minimal delegator that turns a plan into child runs + topology."""

    def __init__(self, coordinator: RunCoordinator) -> None:
        self.coordinator = coordinator

    def delegate_plan(self, parent_run_id: str, plan: Dict) -> Dict:
        parent = self.coordinator.get_run(parent_run_id)
        steps = plan.get("steps", [])
        topology = CoordinationTopology(root_run_id=parent.run_id)
        child_runs: List[RunRecord] = []

        previous_node_id: str | None = None
        for index, step in enumerate(steps, start=1):
            node_id = f"{parent.run_id}-step-{index}"
            child = self.coordinator.create_child_run(
                parent.run_id,
                self._infer_run_type(step),
                owner_agent=step.get("owner_agent"),
                status_message=step.get("description", ""),
            )
            child = self.coordinator.update_run(
                child.run_id,
                stage="delegated",
                status_message=step.get("description", ""),
                metadata={"plan_step": step},
            )
            node = CoordinationNode(
                node_id=node_id,
                kind=step.get("kind", "delegate"),
                name=step.get("name", f"step-{index}"),
                owner_agent=step.get("owner_agent", "default"),
                description=step.get("description", ""),
                run_id=child.run_id,
                depends_on=[previous_node_id] if previous_node_id else [],
            )
            topology.nodes.append(node)
            child_runs.append(child)
            previous_node_id = node.node_id

        self.coordinator.update_run(
            parent.run_id,
            stage="delegated",
            status_message=f"Delegated {len(child_runs)} child run(s).",
            metadata={"coordination_topology": topology.model_dump()},
        )
        return {
            "parent_run": self.coordinator.get_run(parent.run_id),
            "child_runs": child_runs,
            "topology": topology,
        }

    @staticmethod
    def _infer_run_type(step: Dict) -> RunType:
        kind = (step.get("kind") or "").lower()
        if kind == "shortcut":
            return RunType.DIGEST
        if kind == "merge":
            return RunType.SYSTEM
        return RunType.CHAT
