from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


def _parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class SessionConflictError(ValueError):
    pass


@dataclass(slots=True)
class SessionLease:
    session_id: str
    profile_id: str
    client_type: str
    client_id: str
    access_mode: str = "reader"
    status: str = "active"
    lease_until: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "profile_id": self.profile_id,
            "client_type": self.client_type,
            "client_id": self.client_id,
            "access_mode": self.access_mode,
            "status": self.status,
            "lease_until": self.lease_until,
            "metadata": dict(self.metadata or {}),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_expired": _parse_iso(self.lease_until) <= datetime.now(timezone.utc),
        }


class SessionPresenceManager:
    """Minimal session lease manager for multi-end collaboration."""

    def __init__(self) -> None:
        self._items: dict[str, SessionLease] = {}
        self._counter = 0

    def open_session(
        self,
        *,
        profile_id: str,
        client_type: str,
        client_id: str,
        access_mode: str = "reader",
        allow_handover: bool = False,
        lease_seconds: int = 60,
        metadata: dict[str, Any] | None = None,
    ) -> SessionLease:
        normalized_profile = profile_id.strip() or "default"
        normalized_client_type = client_type.strip().lower() or "web"
        normalized_client_id = client_id.strip() or "unknown"
        normalized_mode = access_mode.strip().lower() or "reader"
        if normalized_mode not in {"reader", "writer"}:
            raise ValueError(f"invalid access_mode: {normalized_mode}")
        self._expire_active_sessions()
        if normalized_mode == "writer":
            active_writer = self._find_active_writer(normalized_profile)
            if active_writer is not None and active_writer.client_id != normalized_client_id:
                if not allow_handover:
                    raise SessionConflictError(
                        f"writer conflict: active writer exists for profile `{normalized_profile}` ({active_writer.session_id})"
                    )
                self.release(active_writer.session_id, reason=f"handover_by:{normalized_client_id}")
        self._counter += 1
        now = datetime.now(timezone.utc)
        ttl = max(int(lease_seconds), 1)
        session = SessionLease(
            session_id=f"session-{self._counter:06d}",
            profile_id=normalized_profile,
            client_type=normalized_client_type,
            client_id=normalized_client_id,
            access_mode=normalized_mode,
            status="active",
            lease_until=_to_iso(now + timedelta(seconds=ttl)),
            metadata=dict(metadata or {}),
            created_at=_to_iso(now),
            updated_at=_to_iso(now),
        )
        self._items[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> SessionLease | None:
        session = self._items.get(session_id)
        if session is None:
            return None
        self._sync_expired_status(session)
        return session

    def list_sessions(self, *, profile_id: str | None = None, include_expired: bool = False) -> list[SessionLease]:
        items = list(self._items.values())
        for item in items:
            self._sync_expired_status(item)
        if profile_id:
            items = [item for item in items if item.profile_id == profile_id]
        if not include_expired:
            items = [item for item in items if item.status == "active"]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def heartbeat(self, session_id: str, *, lease_seconds: int = 60) -> SessionLease:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"session not found: {session_id}")
        if session.status != "active":
            raise ValueError(f"session is not active: {session.status}")
        now = datetime.now(timezone.utc)
        ttl = max(int(lease_seconds), 1)
        session.lease_until = _to_iso(now + timedelta(seconds=ttl))
        session.updated_at = _to_iso(now)
        return session

    def release(self, session_id: str, *, reason: str = "manual_release") -> SessionLease:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"session not found: {session_id}")
        now = datetime.now(timezone.utc)
        session.status = "released"
        session.updated_at = _to_iso(now)
        session.metadata = dict(session.metadata or {})
        session.metadata["release_reason"] = reason
        return session

    def _sync_expired_status(self, session: SessionLease) -> None:
        if session.status != "active":
            return
        if _parse_iso(session.lease_until) <= datetime.now(timezone.utc):
            session.status = "expired"
            session.updated_at = utc_now_iso()

    def _find_active_writer(self, profile_id: str) -> SessionLease | None:
        for session in self._items.values():
            self._sync_expired_status(session)
            if session.profile_id == profile_id and session.status == "active" and session.access_mode == "writer":
                return session
        return None

    def _expire_active_sessions(self) -> None:
        for session in self._items.values():
            self._sync_expired_status(session)
