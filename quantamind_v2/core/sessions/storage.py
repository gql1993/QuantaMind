from __future__ import annotations

from quantamind_v2.core.sessions.manager import SessionLease, SessionPresenceManager


class SessionStore:
    """Thin storage facade for session leases."""

    def __init__(self, manager: SessionPresenceManager | None = None) -> None:
        self.manager = manager or SessionPresenceManager()

    def put(self, session: SessionLease) -> SessionLease:
        self.manager._items[session.session_id] = session  # noqa: SLF001
        return session
