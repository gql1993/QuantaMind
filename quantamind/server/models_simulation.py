"""
Simulation workflow models.

Covers the full simulation lifecycle: job creation → queuing → execution →
result collection → quantum parameter extraction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SimJobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SimulationType(str, Enum):
    EIGENMODE = "eigenmode"
    DRIVEN_MODAL = "driven_modal"
    Q3D_CAPACITANCE = "q3d_capacitance"
    LOM = "lom"
    EPR = "epr"
    BLACKBOX_QUANTIZATION = "blackbox_quantization"
    SURROGATE_PREDICT = "surrogate_predict"


class SimulationJob(BaseModel):
    """A simulation job tracked through its lifecycle."""
    job_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    design_id: str = ""
    sim_type: SimulationType = SimulationType.EIGENMODE
    status: SimJobStatus = SimJobStatus.PENDING
    priority: int = 5
    created_at: datetime = Field(default_factory=_utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_node: str = ""
    progress: float = 0.0
    message: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    result_path: str = ""
    error_detail: str = ""

    @property
    def elapsed_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()


class QuantumParameters(BaseModel):
    """Extracted quantum parameters from simulation results."""
    qubit_frequencies_ghz: dict[str, float] = Field(default_factory=dict)
    anharmonicities_mhz: dict[str, float] = Field(default_factory=dict)
    coupling_strengths_mhz: dict[str, float] = Field(default_factory=dict)
    dispersive_shifts_mhz: dict[str, float] = Field(default_factory=dict)
    t1_predictions_us: dict[str, float] = Field(default_factory=dict)
    t2_predictions_us: dict[str, float] = Field(default_factory=dict)
    epr_ratios: dict[str, float] = Field(default_factory=dict)
    capacitance_matrix_fF: Optional[list[list[float]]] = None
    gate_fidelity: dict[str, float] = Field(default_factory=dict)
    crosstalk_matrix: Optional[list[list[float]]] = None


class SurrogateModelPrediction(BaseModel):
    """Result from the AI surrogate model (FFNN/GNN)."""
    model_name: str = ""
    model_version: str = ""
    input_params: dict[str, float] = Field(default_factory=dict)
    predicted_frequency_ghz: Optional[float] = None
    predicted_anharmonicity_mhz: Optional[float] = None
    predicted_t1_us: Optional[float] = None
    confidence: float = 0.0
    inference_time_ms: float = 0.0
