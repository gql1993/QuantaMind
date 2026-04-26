from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from quantamind_v2.agents import build_default_agent_registry
from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.artifacts.renderers import load_and_register_renderers
from quantamind_v2.config import AppSettings
from quantamind_v2.core.approvals import InMemoryApprovalStore
from quantamind_v2.client.shared import (
    InMemoryClientPreferencesStore,
    InMemoryWorkspaceLayoutStore,
    InMemoryWorkspaceRecoveryStore,
)
from quantamind_v2.core.coordination import (
    CoordinationDelegator,
    DualWriteCoordinationAuditStore,
    DualWriteCoordinationPolicyStore,
    FileBackedCoordinationAuditStore,
    FileBackedCoordinationPolicyStore,
    CoordinationMerger,
    CoordinationPlanner,
    CoordinationPolicies,
    CoordinationRouter,
    SQLiteCoordinationAuditStore,
    SQLiteCoordinationPolicyStore,
    CoordinationSupervisor,
)
from quantamind_v2.core.gateway.deps import GatewayDeps, make_filesystem_adapter
from quantamind_v2.core.gateway.routes_client_workspace import build_client_workspace_router
from quantamind_v2.core.gateway.routes_sessions import build_sessions_router
from quantamind_v2.core.gateway.routes_core import build_core_router
from quantamind_v2.core.gateway.routes_memory_planning_integrations import build_memory_planning_integrations_router
from quantamind_v2.core.gateway.routes_runs_artifacts import build_runs_artifacts_router
from quantamind_v2.core.gateway.routes_runtime import build_runtime_router
from quantamind_v2.core.gateway.routes_workflows import build_workflows_router
from quantamind_v2.core.planning import PlanBuilder
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.core.sessions import SessionPresenceManager, SessionTranscriptStore
from quantamind_v2.integrations import KnowledgeAdapter
from quantamind_v2.memory import MemorySyncService
from quantamind_v2.runtimes.mcp import MCPHost, MCPHostPolicy
from quantamind_v2.runtimes.models import ModelRuntimePolicy, ModelRuntimeRouter
from quantamind_v2.runtimes.workers import InMemoryTaskWorker
from quantamind_v2.shortcuts.bootstrap import build_default_shortcut_registry
from quantamind_v2.services import InMemoryLibraryService


PIPELINE_TEMPLATES: dict[str, dict] = {
    "standard_daily_ops": {
        "name": "Standard Daily Ops",
        "description": "Run system status, db status, and intel digest in sequence.",
        "shortcuts": ["system_status", "db_status", "intel_today"],
    }
}


def create_app(
    *,
    coordinator: RunCoordinator | None = None,
    shortcut_registry=None,
    artifact_store: InMemoryArtifactStore | None = None,
    task_worker: InMemoryTaskWorker | None = None,
    approval_store: InMemoryApprovalStore | None = None,
    library_service: InMemoryLibraryService | None = None,
    renderer_registry_config: str | None = None,
    settings: AppSettings | None = None,
) -> FastAPI:
    settings = settings or AppSettings()
    app = FastAPI(
        title=settings.app_name,
        description="QuantaMind 2.0 experimental gateway shell",
        version=settings.app_version,
    )
    coordinator = coordinator or RunCoordinator()
    shortcuts = shortcut_registry or build_default_shortcut_registry()
    artifacts = artifact_store or InMemoryArtifactStore()
    renderer_registry_report = load_and_register_renderers(renderer_registry_config)
    tasks = task_worker or InMemoryTaskWorker(coordinator=coordinator)
    approvals = approval_store or InMemoryApprovalStore()
    library = library_service or InMemoryLibraryService()
    coordination_router = CoordinationRouter(shortcuts)
    agent_registry = build_default_agent_registry()
    coordination_planner = CoordinationPlanner(plan_builder=PlanBuilder(agent_registry=agent_registry))
    coordination_delegator = CoordinationDelegator(coordinator)
    coordination_merger = CoordinationMerger()
    coordination_supervisor = CoordinationSupervisor(
        coordinator=coordinator,
        router=coordination_router,
        planner=coordination_planner,
        delegator=coordination_delegator,
        merger=coordination_merger,
        policies=CoordinationPolicies(),
    )
    state_dir = Path(settings.coordination.state_dir)
    file_audit = FileBackedCoordinationAuditStore(
        state_dir / "coordination_audit.jsonl",
        max_items=settings.coordination.audit_retention_max_events,
        rotate_max_bytes=settings.coordination.audit_rotate_max_bytes,
        rotate_interval_seconds=settings.coordination.audit_rotate_interval_seconds,
        archive_index_path=state_dir / "coordination_audit_archives.json",
    )
    file_policy = FileBackedCoordinationPolicyStore(state_dir / "coordination_policy.json")
    if settings.coordination.dual_write_enabled:
        db_path = Path(settings.coordination.database_path)
        sqlite_audit = SQLiteCoordinationAuditStore(db_path)
        sqlite_policy = SQLiteCoordinationPolicyStore(db_path)
        read_preferred_backend = "sqlite" if settings.coordination.database_read_preferred else "file"
        coordination_audit = DualWriteCoordinationAuditStore(
            file_audit,
            sqlite_audit,
            enabled=True,
            read_preferred_backend=read_preferred_backend,
            fallback_to_primary=settings.coordination.database_read_fallback_to_file,
            profile_allowlist=settings.coordination.database_read_profile_allowlist,
            rollout_percentage=settings.coordination.database_read_rollout_percentage,
        )
        coordination_policy = DualWriteCoordinationPolicyStore(
            file_policy,
            sqlite_policy,
            enabled=True,
            read_preferred_backend=read_preferred_backend,
            fallback_to_primary=settings.coordination.database_read_fallback_to_file,
            profile_allowlist=settings.coordination.database_read_profile_allowlist,
            rollout_percentage=settings.coordination.database_read_rollout_percentage,
        )
    else:
        coordination_audit = file_audit
        coordination_policy = file_policy
    model_runtime = ModelRuntimeRouter(
        policy=ModelRuntimePolicy(
            default_provider=settings.providers.model_default_provider,
            fallback_provider=settings.providers.model_fallback_provider,
            request_timeout_seconds=settings.runtime_limits.default_model_timeout_seconds,
            max_prompt_chars=settings.runtime_limits.default_prompt_budget_chars,
        )
    )
    mcp_host = MCPHost(
        policy=MCPHostPolicy(default_timeout_seconds=settings.runtime_limits.default_mcp_timeout_seconds)
    )
    deps = GatewayDeps(
        settings=settings,
        coordinator=coordinator,
        shortcuts=shortcuts,
        artifacts=artifacts,
        tasks=tasks,
        approvals=approvals,
        library=library,
        coordination_router=coordination_router,
        agent_registry=agent_registry,
        coordination_planner=coordination_planner,
        coordination_supervisor=coordination_supervisor,
        coordination_audit=coordination_audit,
        coordination_policy=coordination_policy,
        model_runtime=model_runtime,
        mcp_host=mcp_host,
        memory_sync=MemorySyncService(),
        filesystem_adapter=make_filesystem_adapter(),
        knowledge_adapter=KnowledgeAdapter(),
        renderer_registry_report=renderer_registry_report,
        pipeline_templates=PIPELINE_TEMPLATES,
        workspace_layouts=InMemoryWorkspaceLayoutStore(),
        client_preferences=InMemoryClientPreferencesStore(),
        workspace_recovery=InMemoryWorkspaceRecoveryStore(),
        session_manager=SessionPresenceManager(),
        session_transcript=SessionTranscriptStore(),
    )
    app.state.renderer_registry = renderer_registry_report
    app.state.model_runtime = model_runtime
    app.state.mcp_host = mcp_host
    app.state.memory_sync = deps.memory_sync
    app.state.filesystem_adapter = deps.filesystem_adapter
    app.state.knowledge_adapter = deps.knowledge_adapter
    app.state.settings = settings
    app.state.agent_registry = agent_registry
    app.state.coordination_persistence_startup = {
        "audit": coordination_audit.get_health_report(),
        "policy": coordination_policy.get_health_report(),
    }

    app.include_router(build_core_router(deps))
    app.include_router(build_runs_artifacts_router(deps))
    app.include_router(build_runtime_router(deps))
    app.include_router(build_memory_planning_integrations_router(deps))
    app.include_router(build_workflows_router(deps))
    app.include_router(build_client_workspace_router(deps))
    app.include_router(build_sessions_router(deps))
    return app


app = create_app()
