from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class CoordinationAuditEvent:
    event_id: str
    event_type: str
    profile_id: str
    strategy: str
    outcome: str
    reason: str
    run_id: str | None = None
    conflict_run_id: str | None = None
    route_mode: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "profile_id": self.profile_id,
            "strategy": self.strategy,
            "outcome": self.outcome,
            "reason": self.reason,
            "run_id": self.run_id,
            "conflict_run_id": self.conflict_run_id,
            "route_mode": self.route_mode,
            "payload": dict(self.payload or {}),
            "created_at": self.created_at,
        }


class CoordinationAuditStore:
    def __init__(self, *, max_items: int = 2000) -> None:
        self._items: list[CoordinationAuditEvent] = []
        self._counter = 0
        self._max_items = max(int(max_items), 100)

    def append(
        self,
        *,
        event_type: str,
        profile_id: str,
        strategy: str,
        outcome: str,
        reason: str,
        run_id: str | None = None,
        conflict_run_id: str | None = None,
        route_mode: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CoordinationAuditEvent:
        self._counter += 1
        event = CoordinationAuditEvent(
            event_id=f"caev-{self._counter:08d}",
            event_type=event_type,
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            reason=reason,
            run_id=run_id,
            conflict_run_id=conflict_run_id,
            route_mode=route_mode,
            payload=dict(payload or {}),
        )
        self._items.append(event)
        if len(self._items) > self._max_items:
            overflow = len(self._items) - self._max_items
            if overflow > 0:
                self._items = self._items[overflow:]
        return event

    def list_events(
        self,
        *,
        profile_id: str | None = None,
        strategy: str | None = None,
        outcome: str | None = None,
        event_type: str | None = None,
        limit: int = 200,
    ) -> list[CoordinationAuditEvent]:
        items = list(self._items)
        if profile_id:
            items = [item for item in items if item.profile_id == profile_id]
        if strategy:
            items = [item for item in items if item.strategy == strategy]
        if outcome:
            items = [item for item in items if item.outcome == outcome]
        if event_type:
            items = [item for item in items if item.event_type == event_type]
        items = sorted(items, key=lambda item: item.created_at, reverse=True)
        return items[: max(limit, 1)]
