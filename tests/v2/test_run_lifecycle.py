from quantamind_v2.contracts.run import RunState
from quantamind_v2.core.runs.lifecycle import RunLifecycle


def test_run_lifecycle_allows_queued_to_running():
    assert RunLifecycle.can_transition(RunState.QUEUED, RunState.RUNNING) is True


def test_run_lifecycle_rejects_completed_to_running():
    assert RunLifecycle.can_transition(RunState.COMPLETED, RunState.RUNNING) is False
