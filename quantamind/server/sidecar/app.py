"""
FastAPI local sidecar server (Application Layer).

Runs as a separate process alongside the PySide6 UI, providing:
  - REST API for design operations
  - WebSocket for real-time updates (canvas ↔ code sync, simulation progress)
  - Bridge between UI layer and Core Engine / QuantaMind

Per V7 spec: Python 3.10+ / FastAPI / uvicorn, port 18800.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from quantamind.server.sidecar.api.design import router as design_router
from quantamind.server.sidecar.api.simulation import router as simulation_router
from quantamind.server.sidecar.api.export import router as export_router
from quantamind.server.sidecar.api.system import router as system_router
from quantamind.server.sidecar.api.quantamind import router as quantamind_router
from quantamind.server.sidecar.api.components import router as components_router
from quantamind.server.services.design_service import DesignService
from quantamind.server.services.component_service import ComponentService
from quantamind.server.services.simulation_service import SimulationService as SimService
from quantamind.server.qeda_bootstrap import get_qeda_config as get_config
from quantamind import APP_DISPLAY_NAME, __version__


class SidecarState:
    """Shared application state accessible to all API routes."""

    def __init__(self) -> None:
        self.design_service = DesignService()
        self.component_service = ComponentService()
        self.simulation_service = SimService()
        self.quantamind_client = None
        self._quantamind_connect_task = None
        self.active_connections: list[Any] = []

    async def startup(self) -> None:
        logger.info("Sidecar services starting up...")
        self.component_service.load_builtin_components()
        logger.info("Sidecar ready.")
        try:
            from quantamind.client.qeda_bridge.client import QuantaMindClient
            from quantamind.client.qeda_bridge.tool_registry import create_default_registry

            self.quantamind_client = QuantaMindClient(tool_registry=create_default_registry())

            async def _connect_quantamind() -> None:
                ok = await self.quantamind_client.connect()
                if not ok:
                    logger.warning("QuantaMind client not connected, chat will be unavailable")

            self._quantamind_connect_task = asyncio.create_task(_connect_quantamind())
        except Exception:
            logger.warning("QuantaMind client initialization failed, chat will be unavailable")

    async def shutdown(self) -> None:
        if self._quantamind_connect_task and not self._quantamind_connect_task.done():
            self._quantamind_connect_task.cancel()
        if self.quantamind_client:
            await self.quantamind_client.disconnect()
        logger.info("Sidecar shutting down...")


state = SidecarState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await state.startup()
    yield
    await state.shutdown()


def create_sidecar_app() -> FastAPI:
    """Factory function to create and configure the FastAPI sidecar application."""

    cfg = get_config().sidecar

    app = FastAPI(
        title=f"{APP_DISPLAY_NAME} Sidecar",
        description="Local application server for Q-EDA design operations",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.sidecar = state

    app.include_router(system_router, prefix="/api/v1", tags=["system"])
    app.include_router(design_router, prefix="/api/v1/designs", tags=["design"])
    app.include_router(simulation_router, prefix="/api/v1/simulations", tags=["simulation"])
    app.include_router(export_router, prefix="/api/v1/export", tags=["export"])
    app.include_router(quantamind_router, prefix="/api/v1/quantamind", tags=["quantamind"])
    app.include_router(components_router, prefix="/api/v1/components", tags=["components"])

    return app


def run_sidecar() -> None:
    """Start the sidecar server (blocking)."""
    import uvicorn

    cfg = get_config().sidecar
    logger.info("Starting Q-EDA Sidecar on {}:{}", cfg.host, cfg.port)

    uvicorn.run(
        create_sidecar_app(),
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level,
        ws_ping_interval=30,
        ws_ping_timeout=30,
    )
