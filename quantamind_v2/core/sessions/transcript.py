from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class SessionEvent:
    event_id: str
    session_id: str
    event_type: str
    actor: str = "system"
    operation: str = ""
    target: str = ""
    source: str = "session"
    severity: str = "info"
    tags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "operation": self.operation,
            "target": self.target,
            "source": self.source,
            "severity": self.severity,
            "tags": list(self.tags),
            "payload": dict(self.payload or {}),
            "created_at": self.created_at,
        }


class SessionTranscriptStore:
    """Store session-level activity events."""

    def __init__(self) -> None:
        self._items: dict[str, list[SessionEvent]] = {}
        self._counter = 0

    def append(
        self,
        session_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        actor: str = "system",
        operation: str = "",
        target: str = "",
        source: str = "session",
        severity: str = "info",
        tags: list[str] | None = None,
    ) -> SessionEvent:
        self._counter += 1
        event = SessionEvent(
            event_id=f"sevt-{self._counter:08d}",
            session_id=session_id,
            event_type=event_type,
            actor=actor,
            operation=operation,
            target=target,
            source=source,
            severity=severity,
            tags=list(tags or []),
            payload=dict(payload or {}),
        )
        self._items.setdefault(session_id, []).append(event)
        return event

    def list_events(
        self,
        session_id: str,
        *,
        event_type: str | None = None,
        source: str | None = None,
        operation: str | None = None,
        limit: int = 200,
    ) -> list[SessionEvent]:
        items = list(self._items.get(session_id, []))
        if event_type:
            items = [item for item in items if item.event_type == event_type]
        if source:
            items = [item for item in items if item.source == source]
        if operation:
            items = [item for item in items if item.operation == operation]
        return items[-max(limit, 1) :]

    def list_all(
        self,
        *,
        source: str | None = None,
        operation: str | None = None,
        profile_id: str | None = None,
        limit: int = 500,
    ) -> list[SessionEvent]:
        flattened: list[SessionEvent] = []
        for events in self._items.values():
            flattened.extend(events)
        if source:
            flattened = [item for item in flattened if item.source == source]
        if operation:
            flattened = [item for item in flattened if item.operation == operation]
        if profile_id:
            flattened = [item for item in flattened if str(item.payload.get("profile_id", "")) == profile_id]
        flattened = sorted(flattened, key=lambda item: item.created_at, reverse=True)
        return flattened[: max(limit, 1)]
