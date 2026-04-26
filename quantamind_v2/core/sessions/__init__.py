"""Session abstractions for QuantaMind 2.0."""

from .manager import SessionConflictError, SessionLease, SessionPresenceManager
from .storage import SessionStore
from .transcript import SessionEvent, SessionTranscriptStore

__all__ = [
    "SessionEvent",
    "SessionConflictError",
    "SessionLease",
    "SessionPresenceManager",
    "SessionStore",
    "SessionTranscriptStore",
]
