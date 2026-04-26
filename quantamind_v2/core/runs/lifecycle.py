from __future__ import annotations

from quantamind_v2.contracts.run import RunState


class RunLifecycle:
    """Small state-transition helper for Phase 1."""

    _ALLOWED = {
        RunState.QUEUED: {RunState.RUNNING, RunState.CANCELLED},
        RunState.RUNNING: {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED},
        RunState.COMPLETED: set(),
        RunState.FAILED: set(),
        RunState.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, current: RunState, target: RunState) -> bool:
        return target in cls._ALLOWED[current]
