from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind_v2.contracts.run import RunState, RunRecord


class CoordinationConflictStrategy(str, Enum):
    QUEUE = "queue"
    REJECT = "reject"
    DEGRADE_SINGLE_AGENT = "degrade_single_agent"


@dataclass(slots=True)
class CoordinationConflictDecision:
    strategy: CoordinationConflictStrategy
    conflict_run_id: str | None
    should_queue: bool
    should_reject: bool
    should_degrade_single_agent: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy.value,
            "conflict_run_id": self.conflict_run_id,
            "should_queue": self.should_queue,
            "should_reject": self.should_reject,
            "should_degrade_single_agent": self.should_degrade_single_agent,
            "reason": self.reason,
        }


def detect_active_coordination_conflict(
    *,
    profile_id: str,
    runs: list[RunRecord],
) -> RunRecord | None:
    for run in sorted(runs, key=lambda item: item.updated_at, reverse=True):
        if run.state != RunState.RUNNING:
            continue
        if str(run.metadata.get("profile_id", "")) != profile_id:
            continue
        if str(run.metadata.get("coordination_role", "")) != "root":
            continue
        return run
    return None


def decide_coordination_conflict(
    *,
    strategy: CoordinationConflictStrategy,
    conflict_run: RunRecord | None,
) -> CoordinationConflictDecision:
    if conflict_run is None:
        return CoordinationConflictDecision(
            strategy=strategy,
            conflict_run_id=None,
            should_queue=False,
            should_reject=False,
            should_degrade_single_agent=False,
            reason="no active conflict detected",
        )
    if strategy == CoordinationConflictStrategy.QUEUE:
        return CoordinationConflictDecision(
            strategy=strategy,
            conflict_run_id=conflict_run.run_id,
            should_queue=True,
            should_reject=False,
            should_degrade_single_agent=False,
            reason=f"active coordination run exists for profile: {conflict_run.run_id}",
        )
    if strategy == CoordinationConflictStrategy.REJECT:
        return CoordinationConflictDecision(
            strategy=strategy,
            conflict_run_id=conflict_run.run_id,
            should_queue=False,
            should_reject=True,
            should_degrade_single_agent=False,
            reason=f"active coordination run exists for profile: {conflict_run.run_id}",
        )
    return CoordinationConflictDecision(
        strategy=strategy,
        conflict_run_id=conflict_run.run_id,
        should_queue=False,
        should_reject=False,
        should_degrade_single_agent=True,
        reason=f"active coordination run exists, degrade to single-agent: {conflict_run.run_id}",
    )
