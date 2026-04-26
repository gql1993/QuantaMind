from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class WorkspaceRecoveryPoint:
    point_id: str
    profile_id: str
    target: str
    layout_id: str
    run_id: str | None = None
    task_id: str | None = None
    artifact_id: str | None = None
    note: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_id": self.point_id,
            "profile_id": self.profile_id,
            "target": self.target,
            "layout_id": self.layout_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "artifact_id": self.artifact_id,
            "note": self.note,
            "metadata": dict(self.metadata or {}),
            "created_at": self.created_at,
        }


class InMemoryWorkspaceRecoveryStore:
    """Store workspace restore points per profile and target."""

    def __init__(self) -> None:
        self._items: dict[str, WorkspaceRecoveryPoint] = {}
        self._order: list[str] = []
        self._counter = 0

    def create(
        self,
        *,
        profile_id: str,
        target: str,
        layout_id: str,
        run_id: str | None = None,
        task_id: str | None = None,
        artifact_id: str | None = None,
        note: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> WorkspaceRecoveryPoint:
        self._counter += 1
        point = WorkspaceRecoveryPoint(
            point_id=f"wrec-{self._counter:06d}",
            profile_id=profile_id.strip() or "default",
            target=target.strip().lower() or "web",
            layout_id=layout_id,
            run_id=run_id,
            task_id=task_id,
            artifact_id=artifact_id,
            note=note.strip(),
            metadata=dict(metadata or {}),
        )
        self._items[point.point_id] = point
        self._order.append(point.point_id)
        return point

    def get(self, point_id: str) -> WorkspaceRecoveryPoint | None:
        return self._items.get(point_id)

    def list(self, *, profile_id: str | None = None, target: str | None = None, limit: int = 50) -> list[WorkspaceRecoveryPoint]:
        ids = list(reversed(self._order))
        results: list[WorkspaceRecoveryPoint] = []
        for point_id in ids:
            point = self._items[point_id]
            if profile_id and point.profile_id != profile_id:
                continue
            if target and point.target != target:
                continue
            results.append(point)
            if len(results) >= max(limit, 1):
                break
        return results

    def latest(self, *, profile_id: str, target: str) -> WorkspaceRecoveryPoint | None:
        items = self.list(profile_id=profile_id, target=target, limit=1)
        return items[0] if items else None
