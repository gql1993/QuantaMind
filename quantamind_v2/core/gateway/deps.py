from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.config import AppSettings
from quantamind_v2.core.approvals import InMemoryApprovalStore
from quantamind_v2.core.coordination import (
    CoordinationPlanner,
    CoordinationRouter,
    CoordinationSupervisor,
)
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.core.sessions import SessionPresenceManager, SessionTranscriptStore
from quantamind_v2.client.shared import InMemoryClientPreferencesStore, InMemoryWorkspaceLayoutStore
from quantamind_v2.client.shared import InMemoryWorkspaceRecoveryStore
from quantamind_v2.integrations import FilesystemAdapter, KnowledgeAdapter
from quantamind_v2.memory import MemorySyncService
from quantamind_v2.runtimes.mcp import MCPHost
from quantamind_v2.runtimes.models import ModelRuntimeRouter
from quantamind_v2.runtimes.workers import InMemoryTaskWorker
from quantamind_v2.services import InMemoryLibraryService


@dataclass(slots=True)
class GatewayDeps:
    settings: AppSettings
    coordinator: RunCoordinator
    shortcuts: Any
    artifacts: InMemoryArtifactStore
    tasks: InMemoryTaskWorker
    approvals: InMemoryApprovalStore
    library: InMemoryLibraryService
    coordination_router: CoordinationRouter
    agent_registry: Any
    coordination_planner: CoordinationPlanner
    coordination_supervisor: CoordinationSupervisor
    coordination_audit: Any
    coordination_policy: Any
    model_runtime: ModelRuntimeRouter
    mcp_host: MCPHost
    memory_sync: MemorySyncService
    filesystem_adapter: FilesystemAdapter
    knowledge_adapter: KnowledgeAdapter
    renderer_registry_report: dict[str, Any]
    pipeline_templates: dict[str, dict]
    workspace_layouts: InMemoryWorkspaceLayoutStore
    client_preferences: InMemoryClientPreferencesStore
    workspace_recovery: InMemoryWorkspaceRecoveryStore
    session_manager: SessionPresenceManager
    session_transcript: SessionTranscriptStore


def infer_artifact_type(shortcut_name: str) -> str:
    if shortcut_name == "intel_today":
        return "intel_report"
    if shortcut_name == "db_status":
        return "db_health_report"
    if shortcut_name == "system_status":
        return "system_diagnosis"
    return "generic_artifact"


def make_filesystem_adapter() -> FilesystemAdapter:
    return FilesystemAdapter(Path.cwd())
