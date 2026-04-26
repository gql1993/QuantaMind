from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import RunRecord, utc_now_iso


@dataclass(slots=True)
class RunMemoryRecord:
    run_id: str
    run_type: str
    state: str
    stage: str
    status_message: str
    owner_agent: str | None
    project_id: str
    artifacts: list[str] = field(default_factory=list)
    event_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_type": self.run_type,
            "state": self.state,
            "stage": self.stage,
            "status_message": self.status_message,
            "owner_agent": self.owner_agent,
            "project_id": self.project_id,
            "artifacts": list(self.artifacts),
            "event_count": self.event_count,
            "metadata": dict(self.metadata or {}),
            "updated_at": self.updated_at,
        }


class InMemoryRunMemoryStore:
    """Minimal run memory index for V2."""

    def __init__(self) -> None:
        self._items: dict[str, RunMemoryRecord] = {}

    def upsert_from_run(self, run: RunRecord, *, event_count: int) -> RunMemoryRecord:
        project_id = str(run.metadata.get("project_id") or "default")
        record = RunMemoryRecord(
            run_id=run.run_id,
            run_type=run.run_type.value,
            state=run.state.value,
            stage=run.stage,
            status_message=run.status_message,
            owner_agent=run.owner_agent,
            project_id=project_id,
            artifacts=list(run.artifacts),
            event_count=event_count,
            metadata=dict(run.metadata or {}),
            updated_at=utc_now_iso(),
        )
        self._items[run.run_id] = record
        return record

    def get(self, run_id: str) -> RunMemoryRecord | None:
        return self._items.get(run_id)
