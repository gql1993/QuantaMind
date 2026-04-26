from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from backend.quantamind_api.services.runtime_state import RuntimeStateService

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


def _runtime_state(request: Request) -> RuntimeStateService:
    return request.app.state.runtime_state


@router.get("")
def list_artifacts(request: Request, run_id: str | None = Query(default=None)) -> dict:
    artifacts = _runtime_state(request).list_artifacts(run_id)
    return {
        "success": True,
        "data": {
            "items": artifacts,
            "total": len(artifacts),
        },
        "error": None,
    }


@router.get("/{artifact_id}")
def get_artifact(request: Request, artifact_id: str) -> dict:
    artifact = _runtime_state(request).get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")
    return {"success": True, "data": artifact, "error": None}
