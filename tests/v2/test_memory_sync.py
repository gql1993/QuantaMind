from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType
from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.memory import MemorySyncService


def test_memory_sync_service_indexes_run_and_project_notes():
    coordinator = RunCoordinator()
    memory = MemorySyncService()
    run = coordinator.create_run(
        RunType.SYSTEM,
        status_message="check system",
    )
    coordinator.append_event(run.run_id, "tool_started", {"tool_name": "system_status"})
    indexed = memory.sync_run(coordinator, run.run_id)
    assert indexed["run_id"] == run.run_id
    assert indexed["event_count"] >= 2
    project_memory = memory.get_project_memory("default")
    assert project_memory["count"] >= 1
    assert "[run]" in project_memory["notes"][-1]["content"]


def test_memory_sync_service_indexes_artifact():
    coordinator = RunCoordinator()
    artifact_store = InMemoryArtifactStore()
    memory = MemorySyncService()
    run = coordinator.create_run(RunType.DIGEST, status_message="digest")
    artifact = ArtifactRecord(
        artifact_id="artifact-test-001",
        run_id=run.run_id,
        artifact_type=ArtifactType.INTEL_REPORT,
        title="intel report",
        summary="daily digest summary",
        payload={"status": "ok", "shortcut": "intel_today"},
    )
    artifact_store.put(artifact)
    indexed = memory.sync_artifact(coordinator, artifact_store, artifact.artifact_id)
    assert indexed["artifact_id"] == artifact.artifact_id
    assert "intel" in indexed["keywords"]
    assert memory.get_artifact_memory(artifact.artifact_id)["title"] == "intel report"
