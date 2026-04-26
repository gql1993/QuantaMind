"""
Simulation orchestration service.

Bridges the Application Layer API with the Core Engine's SimulationManager,
adding business logic like automatic simulation type selection and
result aggregation.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from quantamind.server.qeda_bootstrap import get_qeda_config as get_config
from quantamind.server.qeda_simulation.adapters import (
    HFSSSimulationAdapter,
    MockSimulationAdapter,
    Q3DSimulationAdapter,
)
from quantamind.server.qeda_simulation.manager import SimulationManager
from quantamind.server.qeda_models.simulation import SimJobStatus, SimulationJob, SimulationType


class SimulationService:
    """
    High-level simulation orchestration.

    Implements the 'one-click simulation' workflow:
      LOM quick estimate → Surrogate prediction → Full HFSS → EPR analysis
    """

    def __init__(self) -> None:
        self._manager = SimulationManager()
        self._register_adapters()

    def _register_adapters(self) -> None:
        cfg = get_config().simulation
        self._manager.register_adapter(MockSimulationAdapter())
        self._manager.register_adapter(
            HFSSSimulationAdapter(ansys_version=cfg.ansys_version)
        )
        self._manager.register_adapter(Q3DSimulationAdapter())

    @property
    def manager(self) -> SimulationManager:
        return self._manager

    async def run_quick_estimate(self, design_id: str, **kwargs: Any) -> SimulationJob:
        """Run LOM-based quick frequency estimate."""
        job = SimulationJob(
            design_id=design_id,
            sim_type=SimulationType.LOM,
            config=kwargs,
        )
        return await self._manager.submit_job(job)

    async def run_surrogate_prediction(self, design_id: str, **kwargs: Any) -> SimulationJob:
        """Run AI surrogate model prediction (FFNN/GNN)."""
        job = SimulationJob(
            design_id=design_id,
            sim_type=SimulationType.SURROGATE_PREDICT,
            config=kwargs,
        )
        return await self._manager.submit_job(job)

    async def run_full_simulation(
        self,
        design_id: str,
        sim_type: SimulationType = SimulationType.EIGENMODE,
        **kwargs: Any,
    ) -> SimulationJob:
        """Submit a full electromagnetic simulation (HFSS/Q3D)."""
        job = SimulationJob(
            design_id=design_id,
            sim_type=sim_type,
            config=kwargs,
        )
        return await self._manager.submit_job(job)

    async def run_epr_analysis(self, design_id: str, **kwargs: Any) -> SimulationJob:
        """Run EPR quantum parameter extraction."""
        job = SimulationJob(
            design_id=design_id,
            sim_type=SimulationType.EPR,
            config=kwargs,
        )
        return await self._manager.submit_job(job)

    async def get_job_status(self, job_id: str) -> SimulationJob | None:
        return await self._manager.poll_job(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        return await self._manager.cancel_job(job_id)

    def list_jobs(self, status: Optional[SimJobStatus] = None) -> list[SimulationJob]:
        return self._manager.list_jobs(status)
