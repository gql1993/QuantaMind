from __future__ import annotations

from typing import Any

from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.contracts.artifact import ArtifactRecord
from quantamind_v2.contracts.run import RunRecord
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.memory.artifact_memory import InMemoryArtifactMemoryStore
from quantamind_v2.memory.project_memory import InMemoryProjectMemoryStore
from quantamind_v2.memory.run_memory import InMemoryRunMemoryStore


class MemorySyncService:
    """Bridge for syncing run/artifact snapshots into memory indexes."""

    def __init__(
        self,
        *,
        run_store: InMemoryRunMemoryStore | None = None,
        artifact_store: InMemoryArtifactMemoryStore | None = None,
        project_store: InMemoryProjectMemoryStore | None = None,
    ) -> None:
        self.run_store = run_store or InMemoryRunMemoryStore()
        self.artifact_store = artifact_store or InMemoryArtifactMemoryStore()
        self.project_store = project_store or InMemoryProjectMemoryStore()

    def append_project_note(
        self,
        project_id: str,
        *,
        content: str,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        note = self.project_store.append_note(
            project_id=project_id,
            content=content,
            source=source,
            metadata=metadata,
        )
        return {
            "note_id": note.note_id,
            "project_id": project_id.strip() or "default",
            "content": note.content,
            "source": note.source,
            "metadata": dict(note.metadata or {}),
            "created_at": note.created_at,
        }

    def sync_run(self, coordinator: RunCoordinator, run_id: str) -> dict[str, Any]:
        run = coordinator.get_run(run_id)
        events = coordinator.list_events(run_id)
        indexed = self.run_store.upsert_from_run(run, event_count=len(events))
        project_id = indexed.project_id
        self._append_run_note(project_id, run)
        return indexed.to_dict()

    def sync_artifact(
        self,
        coordinator: RunCoordinator,
        artifacts: InMemoryArtifactStore,
        artifact_id: str,
    ) -> dict[str, Any]:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise KeyError(f"artifact not found: {artifact_id}")
        run = coordinator.get_run(artifact.run_id)
        project_id = str(run.metadata.get("project_id") or "default")
        indexed = self.artifact_store.upsert_from_artifact(artifact, project_id=project_id)
        self._append_artifact_note(project_id, artifact)
        return indexed.to_dict()

    def get_run_memory(self, run_id: str) -> dict[str, Any] | None:
        record = self.run_store.get(run_id)
        return None if record is None else record.to_dict()

    def get_artifact_memory(self, artifact_id: str) -> dict[str, Any] | None:
        record = self.artifact_store.get(artifact_id)
        return None if record is None else record.to_dict()

    def list_artifact_memory(self, *, run_id: str | None = None) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.artifact_store.list(run_id=run_id)]

    def get_project_memory(self, project_id: str) -> dict[str, Any]:
        return self.project_store.get(project_id).to_dict()

    def _append_run_note(self, project_id: str, run: RunRecord) -> None:
        self.project_store.append_note(
            project_id=project_id,
            source="run_sync",
            content=f"[run] {run.run_id} {run.state.value}/{run.stage}: {run.status_message}",
            metadata={"run_id": run.run_id, "run_type": run.run_type.value},
        )

    def _append_artifact_note(self, project_id: str, artifact: ArtifactRecord) -> None:
        self.project_store.append_note(
            project_id=project_id,
            source="artifact_sync",
            content=f"[artifact] {artifact.artifact_id} {artifact.artifact_type.value}: {artifact.title}",
            metadata={"artifact_id": artifact.artifact_id, "run_id": artifact.run_id},
        )
