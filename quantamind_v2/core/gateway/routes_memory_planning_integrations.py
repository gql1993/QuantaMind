from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from quantamind_v2.core.gateway.deps import GatewayDeps
from quantamind_v2.core.gateway.schemas import KnowledgeIndexRequest, PlanningPreviewRequest, ProjectMemoryNoteRequest
from quantamind_v2.core.planning import evaluate_message_heuristics


def build_memory_planning_integrations_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v2/memory/projects/{project_id}/notes")
    async def append_project_memory_note(project_id: str, body: ProjectMemoryNoteRequest) -> dict:
        note = deps.memory_sync.append_project_note(
            project_id,
            content=body.content,
            source=body.source,
            metadata=dict(body.metadata or {}),
        )
        return {"note": note, "project_memory": deps.memory_sync.get_project_memory(project_id)}

    @router.get("/api/v2/memory/projects/{project_id}")
    async def get_project_memory(project_id: str) -> dict:
        return deps.memory_sync.get_project_memory(project_id)

    @router.post("/api/v2/memory/sync/runs/{run_id}")
    async def sync_run_memory(run_id: str) -> dict:
        try:
            record = deps.memory_sync.sync_run(deps.coordinator, run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"run_memory": record}

    @router.get("/api/v2/memory/runs/{run_id}")
    async def get_run_memory(run_id: str) -> dict:
        record = deps.memory_sync.get_run_memory(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"run memory not found: {run_id}")
        return record

    @router.post("/api/v2/memory/sync/artifacts/{artifact_id}")
    async def sync_artifact_memory(artifact_id: str) -> dict:
        try:
            record = deps.memory_sync.sync_artifact(deps.coordinator, deps.artifacts, artifact_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"artifact_memory": record}

    @router.get("/api/v2/memory/artifacts/{artifact_id}")
    async def get_artifact_memory(artifact_id: str) -> dict:
        record = deps.memory_sync.get_artifact_memory(artifact_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"artifact memory not found: {artifact_id}")
        return record

    @router.get("/api/v2/memory/artifacts")
    async def list_artifact_memory(run_id: str | None = Query(default=None)) -> dict:
        return {"items": deps.memory_sync.list_artifact_memory(run_id=run_id)}

    @router.post("/api/v2/planning/preview")
    async def preview_planning(body: PlanningPreviewRequest) -> dict:
        route_result = deps.coordination_router.route(body.message)
        plan = deps.coordination_planner.build_plan(
            body.message,
            route_result,
            priority=body.priority,
            budget_seconds=body.budget_seconds,
        )
        heuristics = evaluate_message_heuristics(
            body.message,
            priority=body.priority,
            budget_seconds=body.budget_seconds,
        )
        return {
            "route_result": {
                "mode": getattr(route_result.get("mode", ""), "value", route_result.get("mode", "")),
                "reason": route_result.get("reason", ""),
            },
            "heuristics": heuristics.to_dict(),
            "plan": {
                **plan,
                "mode": getattr(plan.get("mode", ""), "value", plan.get("mode", "")),
            },
        }

    @router.get("/api/v2/integrations/filesystem/list")
    async def list_filesystem_entries(relative_path: str = Query(default="."), limit: int = Query(default=50)) -> dict:
        try:
            items = deps.filesystem_adapter.list_files(relative_path=relative_path, limit=limit)
        except (PermissionError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"items": items}

    @router.get("/api/v2/integrations/filesystem/read")
    async def read_filesystem_file(relative_path: str = Query(...), max_chars: int = Query(default=4000)) -> dict:
        try:
            content = deps.filesystem_adapter.read_text(relative_path=relative_path, max_chars=max_chars)
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"relative_path": relative_path, "content": content}

    @router.post("/api/v2/integrations/knowledge/index")
    async def index_knowledge_entry(body: KnowledgeIndexRequest) -> dict:
        entry = deps.knowledge_adapter.index(
            title=body.title,
            content=body.content,
            source=body.source,
            metadata=dict(body.metadata or {}),
        )
        return {"entry": entry.to_dict()}

    @router.get("/api/v2/integrations/knowledge/search")
    async def search_knowledge_entries(q: str = Query(default=""), limit: int = Query(default=10)) -> dict:
        items = deps.knowledge_adapter.search(query=q, limit=limit)
        return {"items": [item.to_dict() for item in items]}

    return router
