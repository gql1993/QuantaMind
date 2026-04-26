"""
Design models representing a complete quantum chip design project.

A Design is the top-level container that aggregates:
  - Topology (graph structure)
  - Component instances (placed elements)
  - Routing data (interconnections)
  - Simulation configurations and results
  - Export settings
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from quantamind.server.qeda_models.common import ChipUID, LayerDefinition, DEFAULT_LAYERS
from quantamind.server.qeda_models.component import ComponentInstance
from quantamind.server.qeda_models.topology import Topology


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex[:16]


class DesignState(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SIMULATING = "simulating"
    VALIDATED = "validated"
    EXPORTED = "exported"
    ARCHIVED = "archived"


class RoutingSegment(BaseModel):
    """A single routing segment connecting two component ports."""
    segment_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    source_instance_id: str
    source_port: str
    target_instance_id: str
    target_port: str
    waypoints: list[tuple[float, float]] = Field(default_factory=list)
    layer: int = 1
    width_um: float = 10.0
    gap_um: float = 6.0
    routing_type: str = "cpw"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimulationSetup(BaseModel):
    """Configuration for a simulation run."""
    setup_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    sim_type: str = "eigenmode"
    solver: str = "hfss"
    frequency_range_ghz: tuple[float, float] = (1.0, 10.0)
    num_modes: int = 6
    max_passes: int = 15
    convergence_delta: float = 0.01
    mesh_refinement: int = 3
    target_components: list[str] = Field(default_factory=list)
    custom_settings: dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    """Results from a completed simulation."""
    result_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    setup_id: str = ""
    job_id: str = ""
    status: str = "completed"
    frequencies_ghz: list[float] = Field(default_factory=list)
    capacitance_matrix: Optional[list[list[float]]] = None
    coupling_map: dict[str, float] = Field(default_factory=dict)
    anharmonicities_mhz: dict[str, float] = Field(default_factory=dict)
    t1_predictions_us: dict[str, float] = Field(default_factory=dict)
    s_parameters_path: str = ""
    field_distribution_path: str = ""
    raw_data_path: str = ""
    duration_seconds: float = 0.0
    solver_info: dict[str, Any] = Field(default_factory=dict)


class DRCViolation(BaseModel):
    """A single Design Rule Check violation."""
    rule_name: str
    severity: str = "error"
    message: str = ""
    component_id: str = ""
    location_x: float = 0.0
    location_y: float = 0.0


class ExportConfig(BaseModel):
    """Configuration for design export."""
    format: str = "gds"
    output_path: str = ""
    include_layers: list[int] = Field(default_factory=list)
    precision_nm: float = 1.0
    run_drc_before_export: bool = True
    flatten: bool = False


class DesignMetadata(BaseModel):
    """Metadata for a design."""
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    created_by: str = ""
    description: str = ""
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)
    chip_uid: ChipUID = Field(default_factory=ChipUID)
    target_fab: str = ""
    substrate_material: str = "Si"
    substrate_thickness_um: float = 500.0
    chip_size_x_mm: float = 10.0
    chip_size_y_mm: float = 10.0


class Design(BaseModel):
    """
    Top-level design model: the central data object for a quantum chip design.

    Aggregates topology, component instances, routing, simulation data,
    and export configuration. Corresponds to the Design Model in the
    three-model synchronization architecture (Canvas Model ↔ Design Model ↔ Code Model).
    """
    design_id: str = Field(default_factory=_new_id)
    name: str = "Untitled Design"
    state: DesignState = DesignState.DRAFT
    metadata: DesignMetadata = Field(default_factory=DesignMetadata)
    topology: Topology = Field(default_factory=Topology)
    components: list[ComponentInstance] = Field(default_factory=list)
    routing_segments: list[RoutingSegment] = Field(default_factory=list)
    layers: list[LayerDefinition] = Field(default_factory=lambda: list(DEFAULT_LAYERS))
    simulation_setups: list[SimulationSetup] = Field(default_factory=list)
    simulation_results: list[SimulationResult] = Field(default_factory=list)
    drc_violations: list[DRCViolation] = Field(default_factory=list)
    export_config: ExportConfig = Field(default_factory=ExportConfig)
    project_config: dict[str, Any] = Field(default_factory=dict)

    def get_component(self, instance_id: str) -> ComponentInstance | None:
        for c in self.components:
            if c.instance_id == instance_id:
                return c
        return None

    def get_component_by_name(self, name: str) -> ComponentInstance | None:
        for c in self.components:
            if c.name == name:
                return c
        return None

    def add_component(self, component: ComponentInstance) -> None:
        self.components.append(component)
        self.metadata.updated_at = _utcnow()

    def remove_component(self, instance_id: str) -> bool:
        before = len(self.components)
        self.components = [c for c in self.components if c.instance_id != instance_id]
        if len(self.components) < before:
            self.routing_segments = [
                r for r in self.routing_segments
                if r.source_instance_id != instance_id and r.target_instance_id != instance_id
            ]
            self.metadata.updated_at = _utcnow()
            return True
        return False

    def add_routing(self, segment: RoutingSegment) -> None:
        self.routing_segments.append(segment)
        self.metadata.updated_at = _utcnow()

    @property
    def num_components(self) -> int:
        return len(self.components)

    @property
    def num_routes(self) -> int:
        return len(self.routing_segments)

    @property
    def has_drc_errors(self) -> bool:
        return any(v.severity == "error" for v in self.drc_violations)
