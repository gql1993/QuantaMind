from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator


def test_run_coordinator_creates_run():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="booting")
    assert run.run_type == RunType.SYSTEM
    assert run.state == RunState.QUEUED
    assert run.status_message == "booting"


def test_run_coordinator_transitions_run():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.CHAT)
    updated = coordinator.transition(run.run_id, RunState.RUNNING, stage="routing")
    assert updated.state == RunState.RUNNING
    assert updated.stage == "routing"


def test_run_coordinator_records_events_and_snapshot():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="booting")
    coordinator.transition(run.run_id, RunState.RUNNING, stage="starting")
    coordinator.attach_artifact(run.run_id, "artifact-001")

    events = coordinator.list_events(run.run_id)
    snapshot = coordinator.get_snapshot(run.run_id)

    assert len(events) >= 3
    assert any(event.event_type == "run_created" for event in events)
    assert any(event.event_type == "run_transitioned" for event in events)
    assert any(event.event_type == "artifact_attached" for event in events)
    assert snapshot is not None
    assert snapshot["run_id"] == run.run_id
    assert "artifact-001" in snapshot["artifacts"]
