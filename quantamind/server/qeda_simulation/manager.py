"""
Simulation manager: orchestrates simulation job lifecycle.

Supports both local execution and distributed Celery-based HPC execution.
Adapts to HFSS eigenmode, Q3D capacitance, LOM, EPR, and surrogate model runs.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

from loguru import logger

from quantamind.server.events import SimulationCompleted, SimulationProgress, SimulationSubmitted, get_event_bus
from quantamind.server.qeda_models.simulation import SimJobStatus, SimulationJob, SimulationType


class SimulationAdapter:
    """
    Base adapter for a simulation backend.

    Subclasses implement the actual connection to HFSS, Q3D, etc.
    """

    name: str = "base"
    supported_types: list[SimulationType] = []

    async def submit(self, job: SimulationJob) -> str:
        """Submit a job, returning a backend-specific job handle."""
        raise NotImplementedError

    async def poll_status(self, handle: str) -> tuple[SimJobStatus, float, str]:
        """Poll job status. Returns (status, progress_0_to_1, message)."""
        raise NotImplementedError

    async def fetch_results(self, handle: str, output_dir: str) -> str:
        """Download results. Returns path to result directory."""
        raise NotImplementedError

    async def cancel(self, handle: str) -> None:
        """Cancel a running job."""
        raise NotImplementedError


class SimulationManager:
    """
    Central manager for all simulation activities.

    Maintains a job queue, dispatches to appropriate adapters,
    and publishes events for UI/QuantaMind consumers.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, SimulationAdapter] = {}
        self._jobs: dict[str, SimulationJob] = {}
        self._handles: dict[str, str] = {}
        self._progress_callbacks: dict[str, list[Callable]] = {}

    def register_adapter(self, adapter: SimulationAdapter) -> None:
        self._adapters[adapter.name] = adapter
        logger.info("Registered simulation adapter: {} (types: {})", adapter.name, adapter.supported_types)

    def _find_adapter(self, sim_type: SimulationType) -> SimulationAdapter | None:
        for adapter in self._adapters.values():
            if sim_type in adapter.supported_types:
                return adapter
        return None

    async def submit_job(self, job: SimulationJob) -> SimulationJob:
        """Submit a simulation job for execution."""
        adapter = self._find_adapter(job.sim_type)
        if adapter is None:
            job.status = SimJobStatus.FAILED
            job.error_detail = f"No adapter found for simulation type: {job.sim_type}"
            logger.error(job.error_detail)
            return job

        self._jobs[job.job_id] = job
        job.status = SimJobStatus.QUEUED

        get_event_bus().publish(SimulationSubmitted(
            job_id=job.job_id,
            sim_type=job.sim_type.value,
            source="simulation_manager",
        ))

        try:
            handle = await adapter.submit(job)
            self._handles[job.job_id] = handle
            job.status = SimJobStatus.RUNNING
            logger.info("Submitted job {} via adapter '{}'", job.job_id, adapter.name)
        except Exception as e:
            job.status = SimJobStatus.FAILED
            job.error_detail = str(e)
            logger.exception("Failed to submit job {}", job.job_id)

        return job

    async def poll_job(self, job_id: str) -> SimulationJob | None:
        """Check and update status of a job."""
        job = self._jobs.get(job_id)
        if job is None:
            return None

        handle = self._handles.get(job_id)
        if handle is None:
            return job

        adapter = self._find_adapter(job.sim_type)
        if adapter is None:
            return job

        try:
            status, progress, message = await adapter.poll_status(handle)
            job.status = status
            job.progress = progress
            job.message = message

            get_event_bus().publish(SimulationProgress(
                job_id=job_id,
                progress=progress,
                message=message,
                source="simulation_manager",
            ))

            if status == SimJobStatus.COMPLETED:
                result_path = await adapter.fetch_results(handle, f"results/{job_id}")
                job.result_path = result_path
                get_event_bus().publish(SimulationCompleted(
                    job_id=job_id,
                    success=True,
                    result_path=result_path,
                    source="simulation_manager",
                ))

            elif status == SimJobStatus.FAILED:
                get_event_bus().publish(SimulationCompleted(
                    job_id=job_id,
                    success=False,
                    source="simulation_manager",
                ))

        except Exception:
            logger.exception("Error polling job {}", job_id)

        return job

    async def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        handle = self._handles.get(job_id)
        if job is None or handle is None:
            return False

        adapter = self._find_adapter(job.sim_type)
        if adapter:
            await adapter.cancel(handle)
        job.status = SimJobStatus.CANCELLED
        logger.info("Cancelled job {}", job_id)
        return True

    def get_job(self, job_id: str) -> SimulationJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[SimJobStatus] = None) -> list[SimulationJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
