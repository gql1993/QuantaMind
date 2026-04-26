from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class ProjectMemoryNote:
    note_id: str
    content: str
    source: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class ProjectMemoryRecord:
    project_id: str
    notes: list[ProjectMemoryNote] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "notes": [
                {
                    "note_id": note.note_id,
                    "content": note.content,
                    "source": note.source,
                    "metadata": dict(note.metadata or {}),
                    "created_at": note.created_at,
                }
                for note in self.notes
            ],
            "updated_at": self.updated_at,
            "count": len(self.notes),
        }


class InMemoryProjectMemoryStore:
    """Minimal project memory store for V2."""

    def __init__(self) -> None:
        self._items: dict[str, ProjectMemoryRecord] = {}

    def append_note(
        self,
        project_id: str,
        *,
        content: str,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> ProjectMemoryNote:
        normalized_project_id = project_id.strip() or "default"
        record = self._items.get(normalized_project_id)
        if record is None:
            record = ProjectMemoryRecord(project_id=normalized_project_id)
            self._items[normalized_project_id] = record
        note = ProjectMemoryNote(
            note_id=f"pmem-{len(record.notes) + 1:04d}",
            content=content.strip(),
            source=source,
            metadata=dict(metadata or {}),
        )
        record.notes.append(note)
        record.updated_at = utc_now_iso()
        return note

    def get(self, project_id: str) -> ProjectMemoryRecord:
        normalized_project_id = project_id.strip() or "default"
        record = self._items.get(normalized_project_id)
        if record is None:
            record = ProjectMemoryRecord(project_id=normalized_project_id)
            self._items[normalized_project_id] = record
        return record
