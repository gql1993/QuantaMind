from __future__ import annotations

from uuid import uuid4

from quantamind_v2.contracts.run import RunRecord, RunState, RunType, utc_now_iso
from quantamind_v2.core.runs.events import InMemoryRunEventStore
from quantamind_v2.core.runs.lifecycle import RunLifecycle
from quantamind_v2.core.runs.persistence import InMemoryRunPersistence
from quantamind_v2.core.runs.registry import InMemoryRunRegistry


class RunCoordinator:
    """Phase 1 minimal run coordinator."""

    def __init__(
        self,
        registry: InMemoryRunRegistry | None = None,
        event_store: InMemoryRunEventStore | None = None,
        persistence: InMemoryRunPersistence | None = None,
    ) -> None:
        self.registry = registry or InMemoryRunRegistry()
        self.event_store = event_store or InMemoryRunEventStore()
        self.persistence = persistence or InMemoryRunPersistence()

    def create_run(
        self,
        run_type: RunType,
        *,
        origin: str = "manual",
        parent_run_id: str | None = None,
        owner_agent: str | None = None,
        status_message: str = "",
    ) -> RunRecord:
        run = RunRecord(
            run_id=f"run-{uuid4().hex[:12]}",
            run_type=run_type,
            origin=origin,
            parent_run_id=parent_run_id,
            owner_agent=owner_agent,
            status_message=status_message,
        )
        stored = self.registry.put(run)
        self._record_event(stored.run_id, "run_created", {"run_type": stored.run_type.value, "origin": stored.origin})
        self._persist(stored)
        return stored

    def create_child_run(
        self,
        parent_run_id: str,
        run_type: RunType,
        *,
        origin: str = "delegated",
        owner_agent: str | None = None,
        status_message: str = "",
    ) -> RunRecord:
        parent = self.get_run(parent_run_id)
        child = self.create_run(
            run_type,
            origin=origin,
            parent_run_id=parent.run_id,
            owner_agent=owner_agent,
            status_message=status_message,
        )
        child_ids = list(parent.metadata.get("child_run_ids", []))
        child_ids.append(child.run_id)
        self.update_run(parent.run_id, metadata={"child_run_ids": child_ids})
        return child

    def get_run(self, run_id: str) -> RunRecord:
        run = self.registry.get(run_id)
        if run is None:
            raise KeyError(f"run not found: {run_id}")
        return run

    def list_runs(self) -> list[RunRecord]:
        return self.registry.list()

    def list_events(self, run_id: str):
        return self.event_store.list_for_run(run_id)

    def get_snapshot(self, run_id: str):
        return self.persistence.get(run_id)

    def transition(self, run_id: str, target: RunState, *, stage: str | None = None, status_message: str | None = None) -> RunRecord:
        run = self.get_run(run_id)
        if not RunLifecycle.can_transition(run.state, target):
            raise ValueError(f"invalid transition: {run.state} -> {target}")
        run.state = target
        if stage is not None:
            run.stage = stage
        if status_message is not None:
            run.status_message = status_message
        run.updated_at = utc_now_iso()
        if target in {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}:
            run.completed_at = run.updated_at
        stored = self.registry.put(run)
        self._record_event(
            stored.run_id,
            "run_transitioned",
            {"target": target.value, "stage": stored.stage, "status_message": stored.status_message},
        )
        self._persist(stored)
        return stored

    def update_run(
        self,
        run_id: str,
        *,
        stage: str | None = None,
        status_message: str | None = None,
        metadata: dict | None = None,
    ) -> RunRecord:
        run = self.get_run(run_id)
        if stage is not None:
            run.stage = stage
        if status_message is not None:
            run.status_message = status_message
        if metadata:
            run.metadata.update(metadata)
        run.updated_at = utc_now_iso()
        stored = self.registry.put(run)
        self._record_event(
            stored.run_id,
            "run_updated",
            {"stage": stored.stage, "status_message": stored.status_message, "metadata_keys": sorted((metadata or {}).keys())},
        )
        self._persist(stored)
        return stored

    def attach_artifact(self, run_id: str, artifact_id: str) -> RunRecord:
        run = self.get_run(run_id)
        if artifact_id not in run.artifacts:
            run.artifacts.append(artifact_id)
        run.updated_at = utc_now_iso()
        stored = self.registry.put(run)
        self._record_event(stored.run_id, "artifact_attached", {"artifact_id": artifact_id})
        self._persist(stored)
        return stored

    def append_event(self, run_id: str, event_type: str, payload: dict | None = None) -> RunRecord:
        run = self.get_run(run_id)
        self._record_event(run.run_id, event_type, payload or {})
        refreshed = self.get_run(run_id)
        self._persist(refreshed)
        return refreshed

    def _record_event(self, run_id: str, event_type: str, payload: dict) -> None:
        event = self.event_store.append(run_id, event_type, payload)
        run = self.registry.get(run_id)
        if run is not None:
            run.events.append(event.event_id)
            self.registry.put(run)

    def _persist(self, run: RunRecord) -> None:
        self.persistence.save(run)
