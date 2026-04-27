from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.quantamind_api.routes.dependencies import require_permission
from backend.quantamind_api.services.runtime_state import RuntimeStateService
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def _coordinator(request: Request) -> RunCoordinator:
    return request.app.state.run_coordinator


def _runtime_state(request: Request) -> RuntimeStateService:
    return request.app.state.runtime_state


@router.get("")
def list_runs(request: Request, state: str | None = Query(default=None)) -> dict:
    runs = _runtime_state(request).list_runs()
    if state:
        normalized = state.strip().lower()
        runs = [run for run in runs if run["state"] == normalized]
    return {
        "success": True,
        "data": {
            "items": runs,
            "total": len(runs),
        },
        "error": None,
    }


@router.post("", dependencies=[Depends(require_permission("run:create"))])
def create_run(request: Request, payload: dict | None = None) -> dict:
    data = payload or {}
    run_type = RunType(data.get("run_type", RunType.CHAT.value))
    run = _coordinator(request).create_run(
        run_type,
        origin=data.get("origin", "frontend"),
        owner_agent=data.get("owner_agent"),
        status_message=data.get("status_message", "Created from separated frontend."),
    )
    return {"success": True, "data": run.model_dump(), "error": None}


@router.get("/{run_id}")
def get_run(request: Request, run_id: str) -> dict:
    run = _runtime_state(request).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return {"success": True, "data": run, "error": None}


@router.get("/{run_id}/events")
def list_run_events(request: Request, run_id: str) -> dict:
    if _runtime_state(request).get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    events = _runtime_state(request).list_events(run_id)
    return {
        "success": True,
        "data": {"items": events, "total": len(events)},
        "error": None,
    }


@router.post("/{run_id}/cancel", dependencies=[Depends(require_permission("run:cancel"))])
def cancel_run(request: Request, run_id: str) -> dict:
    if run_id.startswith("v1-"):
        raise HTTPException(status_code=409, detail="V1 compatible runs are read-only from separated API")
    try:
        run = _coordinator(request).transition(
            run_id,
            RunState.CANCELLED,
            stage="cancelled",
            status_message="Cancelled from frontend.",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc
    return {"success": True, "data": run.model_dump(), "error": None}


@router.post("/{run_id}/retry", dependencies=[Depends(require_permission("run:retry"))])
def retry_run(request: Request, run_id: str) -> dict:
    if run_id.startswith("v1-"):
        raise HTTPException(status_code=409, detail="V1 compatible runs are read-only from separated API")
    try:
        source = _coordinator(request).get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc
    retry = _coordinator(request).create_run(
        source.run_type,
        origin="retry",
        parent_run_id=source.run_id,
        owner_agent=source.owner_agent,
        status_message=f"Retry created for {source.run_id}.",
    )
    return {"success": True, "data": retry.model_dump(), "error": None}
