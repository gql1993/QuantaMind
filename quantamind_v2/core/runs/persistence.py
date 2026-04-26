from __future__ import annotations

from typing import Dict, Optional

from quantamind_v2.contracts.run import RunRecord


class InMemoryRunPersistence:
    """Phase 1 snapshot persistence for run records."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, dict] = {}

    def save(self, run: RunRecord) -> dict:
        snapshot = run.model_dump()
        self._snapshots[run.run_id] = snapshot
        return snapshot

    def get(self, run_id: str) -> Optional[dict]:
        snap = self._snapshots.get(run_id)
        return dict(snap) if snap is not None else None
