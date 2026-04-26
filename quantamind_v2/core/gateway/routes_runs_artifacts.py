from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from quantamind_v2.artifacts.renderers import list_registered_renderers
from quantamind_v2.client.shared import build_shared_client_state
from quantamind_v2.core.gateway.deps import GatewayDeps


def build_runs_artifacts_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v2/runs")
    async def list_runs() -> dict:
        return {"runs": [run.model_dump() for run in deps.coordinator.list_runs()]}

    @router.get("/api/v2/runs/{run_id}")
    async def get_run(run_id: str) -> dict:
        try:
            run = deps.coordinator.get_run(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return run.model_dump()

    @router.get("/api/v2/runs/{run_id}/events")
    async def list_run_events(run_id: str) -> dict:
        try:
            deps.coordinator.get_run(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        events = deps.coordinator.list_events(run_id)
        return {"items": [event.model_dump() for event in events]}

    @router.get("/api/v2/runs/{run_id}/snapshot")
    async def get_run_snapshot(run_id: str) -> dict:
        try:
            deps.coordinator.get_run(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        snapshot = deps.coordinator.get_snapshot(run_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail=f"snapshot not found: {run_id}")
        return {"snapshot": snapshot}

    @router.get("/api/v2/console/runs")
    async def list_console_runs(state: str | None = Query(default=None)) -> dict:
        runs = deps.coordinator.list_runs()
        if state:
            normalized = state.strip().lower()
            runs = [run for run in runs if run.state.value == normalized]
        runs = sorted(runs, key=lambda item: item.updated_at, reverse=True)
        items = []
        for run in runs:
            run_events = deps.coordinator.list_events(run.run_id)
            items.append(
                {
                    "run": run.model_dump(),
                    "event_count": len(run_events),
                    "latest_event": run_events[-1].model_dump() if run_events else None,
                    "artifact_count": len(run.artifacts),
                }
            )
        return {"items": items}

    @router.get("/api/v2/client/shared/state")
    async def get_client_shared_state() -> dict:
        runs = sorted(deps.coordinator.list_runs(), key=lambda item: item.updated_at, reverse=True)
        tasks_items = sorted(deps.tasks.list(), key=lambda item: item.updated_at, reverse=True)
        artifact_items = sorted(deps.artifacts.list(), key=lambda item: item.created_at, reverse=True)
        run_payloads = [item.model_dump() for item in runs]
        task_payloads = [item.model_dump() for item in tasks_items]
        artifact_payloads = [item.model_dump() for item in artifact_items]
        event_counts = {run.run_id: len(deps.coordinator.list_events(run.run_id)) for run in runs}
        state = build_shared_client_state(
            runs=run_payloads,
            tasks=task_payloads,
            artifacts=artifact_payloads,
            run_event_counts=event_counts,
        )
        return {"state": state.to_dict()}

    @router.get("/api/v2/artifacts")
    async def list_artifacts(run_id: str | None = Query(default=None)) -> dict:
        items = deps.artifacts.list_for_run(run_id) if run_id else deps.artifacts.list()
        return {"items": [item.model_dump() for item in items]}

    @router.get("/api/v2/artifacts/{artifact_id}")
    async def get_artifact(artifact_id: str) -> dict:
        artifact = deps.artifacts.get(artifact_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail=f"artifact not found: {artifact_id}")
        return artifact.model_dump()

    @router.get("/api/v2/artifacts/{artifact_id}/view")
    async def get_artifact_view(artifact_id: str) -> dict:
        artifact = deps.artifacts.get(artifact_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail=f"artifact not found: {artifact_id}")
        from quantamind_v2.artifacts import render_artifact_text

        return render_artifact_text(artifact).model_dump()

    @router.get("/api/v2/artifacts/renderers/registry")
    async def get_renderer_registry() -> dict:
        return {
            "loader": deps.renderer_registry_report,
            "active_renderers": list_registered_renderers(),
        }

    @router.get("/api/v2/runs/{run_id}/artifacts")
    async def list_run_artifacts(run_id: str) -> dict:
        try:
            deps.coordinator.get_run(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"items": [item.model_dump() for item in deps.artifacts.list_for_run(run_id)]}

    return router
