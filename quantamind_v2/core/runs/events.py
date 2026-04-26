from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from quantamind_v2.contracts.event import RunEvent


class InMemoryRunEventStore:
    """Phase 1 in-memory run event store."""

    def __init__(self) -> None:
        self._events_by_run: Dict[str, List[RunEvent]] = {}

    def append(self, run_id: str, event_type: str, payload: dict | None = None) -> RunEvent:
        event = RunEvent(
            event_id=f"event-{uuid4().hex[:12]}",
            run_id=run_id,
            event_type=event_type,
            payload=payload or {},
        )
        self._events_by_run.setdefault(run_id, []).append(event)
        return event

    def list_for_run(self, run_id: str) -> List[RunEvent]:
        return list(self._events_by_run.get(run_id, []))
