from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.quantamind_api.routes.agents import router as agents_router
from backend.quantamind_api.routes.artifacts import router as artifacts_router
from backend.quantamind_api.routes.chat import router as chat_router
from backend.quantamind_api.routes.data import router as data_router
from backend.quantamind_api.routes.health import router as health_router
from backend.quantamind_api.routes.knowledge import router as knowledge_router
from backend.quantamind_api.routes.permissions import router as permissions_router
from backend.quantamind_api.routes.runs import router as runs_router
from backend.quantamind_api.routes.system import router as system_router
from backend.quantamind_api.services.chat_service import ChatService
from backend.quantamind_api.services.runtime_state import RuntimeStateService
from backend.quantamind_api.settings import ApiSettings
from quantamind_v2.agents import build_default_agent_registry
from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or ApiSettings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Separated API shell for the QuantaMind AI research platform.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _configure_state(app)
    app.include_router(health_router)
    app.include_router(system_router)
    app.include_router(permissions_router)
    app.include_router(chat_router)
    app.include_router(runs_router)
    app.include_router(artifacts_router)
    app.include_router(agents_router)
    app.include_router(data_router)
    app.include_router(knowledge_router)
    return app


def _configure_state(app: FastAPI) -> None:
    coordinator = RunCoordinator()
    artifacts = InMemoryArtifactStore()
    agents = build_default_agent_registry()
    _seed_demo_state(coordinator, artifacts)
    app.state.run_coordinator = coordinator
    app.state.artifact_store = artifacts
    app.state.agent_registry = agents
    app.state.runtime_state = RuntimeStateService(coordinator, artifacts)
    app.state.chat_service = ChatService(coordinator)


def _seed_demo_state(coordinator: RunCoordinator, artifacts: InMemoryArtifactStore) -> None:
    design_run = coordinator.create_run(
        RunType.SIMULATION,
        origin="demo",
        owner_agent="design_specialist",
        status_message="芯片设计参数优化任务正在执行。",
    )
    design_run = coordinator.transition(
        design_run.run_id,
        RunState.RUNNING,
        stage="design_analysis",
        status_message="正在进行设计参数分析与规则检查。",
    )
    design_artifact = artifacts.put(
        ArtifactRecord(
            artifact_id="artifact-design-risk-demo",
            run_id=design_run.run_id,
            artifact_type=ArtifactType.COORDINATION_REPORT,
            title="超导量子芯片设计风险初评",
            summary="展示前后端分离后 Artifact API 的演示产物。",
            payload={"risk_level": "medium", "source": "backend-demo-seed"},
        )
    )
    coordinator.attach_artifact(design_run.run_id, design_artifact.artifact_id)

    data_run = coordinator.create_run(
        RunType.DATA_SYNC,
        origin="demo",
        owner_agent="data_analyst",
        status_message="跨域数据分析样例已完成。",
    )
    data_run = coordinator.transition(
        data_run.run_id,
        RunState.RUNNING,
        stage="data_analysis",
        status_message="正在汇总跨域数据。",
    )
    coordinator.transition(
        data_run.run_id,
        RunState.COMPLETED,
        stage="summary",
        status_message="已生成数据分析摘要。",
    )
    artifacts.put(
        ArtifactRecord(
            artifact_id="artifact-data-summary-demo",
            run_id=data_run.run_id,
            artifact_type=ArtifactType.DB_HEALTH_REPORT,
            title="设计-制造-测控跨域数据摘要",
            summary="用于前端产物中心的演示数据。",
            payload={"domains": ["design", "manufacturing", "measurement"]},
        )
    )


app = create_app()


if __name__ == "__main__":
    settings = ApiSettings()
    uvicorn.run("backend.quantamind_api.app:app", host=settings.host, port=settings.port, reload=True)
