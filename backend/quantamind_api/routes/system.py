from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/system", tags=["admin-system"])


@router.get("/status")
def system_status() -> dict:
    return {
        "success": True,
        "data": {
            "gateway": {"status": "ok", "label": "FastAPI Gateway"},
            "frontend": {"status": "separated", "label": "Vite React Workspace"},
            "runtime": {"status": "compat", "label": "V1/V2 compatibility shell"},
        },
        "error": None,
    }
