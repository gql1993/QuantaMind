"""
System-level API endpoints: health check, status, configuration.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from quantamind import APP_DISPLAY_NAME, __version__

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "application": APP_DISPLAY_NAME,
        "version": __version__,
    }


@router.get("/status")
async def system_status(request: Request) -> dict:
    sidecar = request.app.state.sidecar
    designs = sidecar.design_service.list_designs()
    active = sidecar.design_service.active_design

    return {
        "version": __version__,
        "designs_open": len(designs),
        "active_design": active.name if active else None,
        "components_in_library": sidecar.component_service.count,
        "active_simulations": len(
            sidecar.simulation_service.list_jobs()
        ),
    }
