from __future__ import annotations

from fastapi import APIRouter

from quantamind_v2.core.gateway.deps import GatewayDeps


def build_core_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": "QuantaMind Gateway V2"}

    @router.get("/api/v2/config/summary")
    async def get_config_summary() -> dict:
        return deps.settings.to_dict()

    @router.get("/api/v2/agents/profiles")
    async def list_agent_profiles() -> dict:
        return {"items": [item.to_dict() for item in deps.agent_registry.list()]}

    return router
