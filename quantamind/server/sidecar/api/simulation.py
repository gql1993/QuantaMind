"""
Simulation REST API endpoints.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from quantamind.server.qeda_models.simulation import SimulationType

router = APIRouter()


class RunSimulationRequest(BaseModel):
    design_id: str
    sim_type: str = "eigenmode"
    config: dict[str, Any] = Field(default_factory=dict)


def _get_service(request: Request):
    return request.app.state.sidecar.simulation_service


@router.post("/run")
async def run_simulation(req: RunSimulationRequest, request: Request) -> dict:
    svc = _get_service(request)
    sim_type = SimulationType(req.sim_type)

    if sim_type == SimulationType.LOM:
        job = await svc.run_quick_estimate(req.design_id, **req.config)
    elif sim_type == SimulationType.SURROGATE_PREDICT:
        job = await svc.run_surrogate_prediction(req.design_id, **req.config)
    elif sim_type == SimulationType.EPR:
        job = await svc.run_epr_analysis(req.design_id, **req.config)
    else:
        job = await svc.run_full_simulation(req.design_id, sim_type, **req.config)

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "sim_type": job.sim_type.value,
    }


@router.get("/jobs")
async def list_jobs(request: Request, status: Optional[str] = None) -> list[dict]:
    svc = _get_service(request)
    from quantamind.server.qeda_models.simulation import SimJobStatus

    filter_status = SimJobStatus(status) if status else None
    jobs = svc.list_jobs(filter_status)
    return [
        {
            "job_id": j.job_id,
            "design_id": j.design_id,
            "sim_type": j.sim_type.value,
            "status": j.status.value,
            "progress": j.progress,
            "message": j.message,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> dict:
    svc = _get_service(request)
    job = await svc.get_job_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json")


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request) -> dict:
    svc = _get_service(request)
    if not await svc.cancel_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "cancelled"}
