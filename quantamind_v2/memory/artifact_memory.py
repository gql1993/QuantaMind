from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.artifact import ArtifactRecord
from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class ArtifactMemoryRecord:
    artifact_id: str
    run_id: str
    artifact_type: str
    title: str
    summary: str
    project_id: str = "default"
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "run_id": self.run_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "summary": self.summary,
            "project_id": self.project_id,
            "keywords": list(self.keywords),
            "metadata": dict(self.metadata or {}),
            "updated_at": self.updated_at,
        }


class InMemoryArtifactMemoryStore:
    """Minimal artifact memory index for V2."""

    def __init__(self) -> None:
        self._items: dict[str, ArtifactMemoryRecord] = {}

    def upsert_from_artifact(
        self,
        artifact: ArtifactRecord,
        *,
        project_id: str = "default",
    ) -> ArtifactMemoryRecord:
        keywords = _extract_keywords(artifact)
        record = ArtifactMemoryRecord(
            artifact_id=artifact.artifact_id,
            run_id=artifact.run_id,
            artifact_type=artifact.artifact_type.value,
            title=artifact.title,
            summary=artifact.summary,
            project_id=project_id,
            keywords=keywords,
            metadata={"created_at": artifact.created_at},
            updated_at=utc_now_iso(),
        )
        self._items[artifact.artifact_id] = record
        return record

    def get(self, artifact_id: str) -> ArtifactMemoryRecord | None:
        return self._items.get(artifact_id)

    def list(self, *, run_id: str | None = None) -> list[ArtifactMemoryRecord]:
        items = list(self._items.values())
        if run_id:
            items = [item for item in items if item.run_id == run_id]
        return items


def _extract_keywords(artifact: ArtifactRecord) -> list[str]:
    chunks = [
        artifact.artifact_type.value,
        artifact.title,
        artifact.summary,
        str(artifact.payload.get("status", "")),
        str(artifact.payload.get("shortcut", "")),
    ]
    words: list[str] = []
    for chunk in chunks:
        for token in str(chunk).replace("_", " ").split():
            normalized = token.strip().lower()
            if normalized and normalized not in words:
                words.append(normalized)
    return words[:16]
