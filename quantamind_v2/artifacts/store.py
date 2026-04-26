from __future__ import annotations

from typing import Dict, List, Optional

from quantamind_v2.contracts.artifact import ArtifactRecord


class InMemoryArtifactStore:
    """Phase 1 in-memory artifact store."""

    def __init__(self) -> None:
        self._items: Dict[str, ArtifactRecord] = {}

    def put(self, artifact: ArtifactRecord) -> ArtifactRecord:
        self._items[artifact.artifact_id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Optional[ArtifactRecord]:
        return self._items.get(artifact_id)

    def list(self) -> List[ArtifactRecord]:
        return list(self._items.values())

    def list_for_run(self, run_id: str) -> List[ArtifactRecord]:
        return [artifact for artifact in self._items.values() if artifact.run_id == run_id]
