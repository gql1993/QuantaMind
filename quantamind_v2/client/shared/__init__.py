"""Shared client contracts for Web/Desktop shells."""

from .models import SharedArtifactView, SharedClientState, SharedRunView, SharedTaskView
from .normalizers import (
    build_shared_client_state,
    normalize_artifact,
    normalize_run,
    normalize_task,
)
from .preferences import ClientPreferences, InMemoryClientPreferencesStore
from .recovery import InMemoryWorkspaceRecoveryStore, WorkspaceRecoveryPoint
from .workspace import InMemoryWorkspaceLayoutStore, WorkspaceLayout, WorkspacePanel

__all__ = [
    "ClientPreferences",
    "InMemoryClientPreferencesStore",
    "InMemoryWorkspaceRecoveryStore",
    "InMemoryWorkspaceLayoutStore",
    "SharedArtifactView",
    "SharedClientState",
    "SharedRunView",
    "SharedTaskView",
    "WorkspaceLayout",
    "WorkspacePanel",
    "WorkspaceRecoveryPoint",
    "build_shared_client_state",
    "normalize_artifact",
    "normalize_run",
    "normalize_task",
]
