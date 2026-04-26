from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {
        "success": True,
        "data": {
            "service": "quantamind-api",
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "error": None,
    }
