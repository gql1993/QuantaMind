"""
Component data models for the Q-EDA element library.

Components are parameterized quantum circuit elements (qubits, couplers,
resonators, etc.) defined by JSON Schema and stored in the local component
library with optional cloud sync to QuantaMind's Memory knowledge graph.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid4().hex[:12]


class ComponentCategory(str, Enum):
    QUBIT = "qubit"
    COUPLER = "coupler"
    RESONATOR = "resonator"
    CONTROL_LINE = "control_line"
    READOUT_LINE = "readout_line"
    AIRBRIDGE = "airbridge"
    LAUNCH_PAD = "launch_pad"
    JUNCTION = "junction"
    FLUX_LINE = "flux_line"
    CUSTOM = "custom"


class QubitType(str, Enum):
    TRANSMON = "transmon"
    XMON = "xmon"
    FLUXONIUM = "fluxonium"
    GATEMON = "gatemon"
    CHARGE_QUBIT = "charge_qubit"
    CUSTOM = "custom"


class CouplerType(str, Enum):
    CAPACITIVE = "capacitive"
    INDUCTIVE = "inductive"
    TUNABLE = "tunable"
    DIRECT = "direct"
    BUS_RESONATOR = "bus_resonator"
    CUSTOM = "custom"


class ParameterType(str, Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    ENUM = "enum"


class ComponentParameter(BaseModel):
    """Single parameter definition for a component."""
    name: str
    display_name: str = ""
    param_type: ParameterType = ParameterType.FLOAT
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    description: str = ""
    enum_values: Optional[list[str]] = None
    linked_params: list[str] = Field(default_factory=list)

    def validate_value(self, value: Any) -> bool:
        if self.param_type == ParameterType.FLOAT:
            try:
                v = float(value)
            except (TypeError, ValueError):
                return False
            if self.min_value is not None and v < self.min_value:
                return False
            if self.max_value is not None and v > self.max_value:
                return False
            return True
        if self.param_type == ParameterType.ENUM:
            return value in (self.enum_values or [])
        return True


class PortDefinition(BaseModel):
    """Connection port on a component."""
    name: str
    direction: str = "inout"
    position_offset_x: float = 0.0
    position_offset_y: float = 0.0
    orientation: float = 0.0
    impedance_ohm: float = 50.0


class ComponentDefinition(BaseModel):
    """
    Full definition of a library component (the "template").

    This maps to the element JSON Schema stored in the component library
    and synced with QuantaMind's Memory L3 knowledge graph.
    """
    component_id: str = Field(default_factory=_new_id)
    name: str
    category: ComponentCategory
    subcategory: str = ""
    version: str = "1.0.0"
    description: str = ""
    parameters: list[ComponentParameter] = Field(default_factory=list)
    ports: list[PortDefinition] = Field(default_factory=list)
    generator_class: str = ""
    geometry_engine: str = "gdstk"
    thumbnail_svg: str = ""
    tags: list[str] = Field(default_factory=list)
    documentation_url: str = ""

    def get_parameter(self, name: str) -> ComponentParameter | None:
        for p in self.parameters:
            if p.name == name:
                return p
        return None

    def default_values(self) -> dict[str, Any]:
        return {p.name: p.default for p in self.parameters}


class ComponentInstance(BaseModel):
    """
    An instantiated component placed on the chip canvas.

    Holds the runtime parameter values and position. Modifications trigger
    bidirectional sync (Canvas ↔ Code ↔ Design Model).
    """
    instance_id: str = Field(default_factory=_new_id)
    definition_id: str
    name: str
    position_x: float = 0.0
    position_y: float = 0.0
    rotation: float = 0.0
    mirror_x: bool = False
    mirror_y: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)
    layer_overrides: dict[str, int] = Field(default_factory=dict)
    locked: bool = False
    visible: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def position(self) -> tuple[float, float]:
        return (self.position_x, self.position_y)


# --- Pre-built component definitions for common quantum elements ---

XMON_TRANSMON = ComponentDefinition(
    name="Xmon Transmon",
    category=ComponentCategory.QUBIT,
    subcategory=QubitType.XMON,
    description="Cross-shaped transmon qubit with four capacitive arms",
    parameters=[
        ComponentParameter(
            name="cross_width", display_name="Cross Width",
            default=0.02, min_value=0.005, max_value=0.1, unit="mm",
            description="Width of the cross arms",
        ),
        ComponentParameter(
            name="cross_length", display_name="Cross Length",
            default=0.2, min_value=0.05, max_value=0.5, unit="mm",
            description="Length of the cross arms",
        ),
        ComponentParameter(
            name="cross_gap", display_name="Cross Gap",
            default=0.02, min_value=0.005, max_value=0.05, unit="mm",
            description="Gap between cross and ground plane",
        ),
        ComponentParameter(
            name="jj_area", display_name="JJ Area",
            default=0.04, min_value=0.01, max_value=0.2, unit="um²",
            description="Josephson junction area",
        ),
    ],
    ports=[
        PortDefinition(name="port_N", position_offset_y=0.2, orientation=90),
        PortDefinition(name="port_S", position_offset_y=-0.2, orientation=270),
        PortDefinition(name="port_E", position_offset_x=0.2, orientation=0),
        PortDefinition(name="port_W", position_offset_x=-0.2, orientation=180),
    ],
    generator_class="quantamind.server.geometry.generators.XmonGenerator",
    tags=["transmon", "xmon", "superconducting"],
)

CPW_RESONATOR = ComponentDefinition(
    name="CPW Resonator",
    category=ComponentCategory.RESONATOR,
    description="Coplanar waveguide (CPW) λ/4 readout resonator",
    parameters=[
        ComponentParameter(
            name="total_length", display_name="Total Length",
            default=5.0, min_value=1.0, max_value=20.0, unit="mm",
        ),
        ComponentParameter(
            name="center_width", display_name="Center Width",
            default=0.01, min_value=0.002, max_value=0.05, unit="mm",
        ),
        ComponentParameter(
            name="gap_width", display_name="Gap Width",
            default=0.006, min_value=0.002, max_value=0.02, unit="mm",
        ),
        ComponentParameter(
            name="coupling_length", display_name="Coupling Length",
            default=0.3, min_value=0.05, max_value=1.0, unit="mm",
        ),
    ],
    ports=[
        PortDefinition(name="port_in", orientation=180),
        PortDefinition(name="port_out", orientation=0),
    ],
    generator_class="quantamind.server.geometry.generators.CPWResonatorGenerator",
    tags=["resonator", "cpw", "readout"],
)

TUNABLE_COUPLER = ComponentDefinition(
    name="Tunable Coupler",
    category=ComponentCategory.COUPLER,
    subcategory=CouplerType.TUNABLE,
    description="Frequency-tunable coupler with SQUID loop",
    parameters=[
        ComponentParameter(
            name="pad_width", display_name="Pad Width",
            default=0.1, min_value=0.02, max_value=0.3, unit="mm",
        ),
        ComponentParameter(
            name="pad_height", display_name="Pad Height",
            default=0.08, min_value=0.02, max_value=0.2, unit="mm",
        ),
        ComponentParameter(
            name="coupling_gap", display_name="Coupling Gap",
            default=0.01, min_value=0.002, max_value=0.05, unit="mm",
        ),
    ],
    ports=[
        PortDefinition(name="port_A", position_offset_x=-0.1, orientation=180),
        PortDefinition(name="port_B", position_offset_x=0.1, orientation=0),
        PortDefinition(name="port_flux", position_offset_y=-0.08, orientation=270),
    ],
    generator_class="quantamind.server.geometry.generators.TunableCouplerGenerator",
    tags=["coupler", "tunable", "squid"],
)
