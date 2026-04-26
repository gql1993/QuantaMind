"""
Shared types, enums, and base models used across the Q-EDA domain.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uid() -> str:
    return uuid4().hex[:16]


class Point2D(BaseModel):
    """2D coordinate in meters."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Point2D) -> Point2D:
        return Point2D(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Point2D) -> Point2D:
        return Point2D(x=self.x - other.x, y=self.y - other.y)

    def distance_to(self, other: Point2D) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


class Point3D(BaseModel):
    """3D coordinate in meters."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class BoundingBox(BaseModel):
    """Axis-aligned bounding box."""
    min_point: Point2D = Field(default_factory=Point2D)
    max_point: Point2D = Field(default_factory=Point2D)

    @property
    def width(self) -> float:
        return self.max_point.x - self.min_point.x

    @property
    def height(self) -> float:
        return self.max_point.y - self.min_point.y

    @property
    def center(self) -> Point2D:
        return Point2D(
            x=(self.min_point.x + self.max_point.x) / 2,
            y=(self.min_point.y + self.max_point.y) / 2,
        )

    def contains(self, point: Point2D) -> bool:
        return (
            self.min_point.x <= point.x <= self.max_point.x
            and self.min_point.y <= point.y <= self.max_point.y
        )

    def intersects(self, other: BoundingBox) -> bool:
        return not (
            self.max_point.x < other.min_point.x
            or self.min_point.x > other.max_point.x
            or self.max_point.y < other.min_point.y
            or self.min_point.y > other.max_point.y
        )


class ChipUID(BaseModel):
    """Globally unique chip identifier for cross-domain traceability."""
    uid: str = Field(default_factory=_new_uid)
    batch_id: str = ""
    wafer_id: str = ""
    die_position: str = ""


class MaterialType(str, Enum):
    ALUMINUM = "Al"
    NIOBIUM = "Nb"
    NIOBIUM_NITRIDE = "NbN"
    NIOBIUM_TITANIUM_NITRIDE = "NbTiN"
    TANTALUM = "Ta"
    SILICON = "Si"
    SAPPHIRE = "Al2O3"
    CUSTOM = "custom"


class LayerDefinition(BaseModel):
    """GDS layer definition for chip fabrication."""
    name: str
    gds_layer: int
    gds_datatype: int = 0
    material: MaterialType = MaterialType.ALUMINUM
    thickness_nm: float = 0.0
    description: str = ""
    color: str = "#4A90D9"
    visible: bool = True
    editable: bool = True


DEFAULT_LAYERS: list[LayerDefinition] = [
    LayerDefinition(
        name="ground_plane",
        gds_layer=0,
        material=MaterialType.ALUMINUM,
        thickness_nm=100.0,
        description="Ground plane (superconducting metal)",
        color="#C8C8C8",
    ),
    LayerDefinition(
        name="trace",
        gds_layer=1,
        material=MaterialType.ALUMINUM,
        thickness_nm=100.0,
        description="Signal traces and CPW center conductors",
        color="#4A90D9",
    ),
    LayerDefinition(
        name="junction",
        gds_layer=2,
        material=MaterialType.ALUMINUM,
        thickness_nm=50.0,
        description="Josephson junction layer",
        color="#E74C3C",
    ),
    LayerDefinition(
        name="bandage",
        gds_layer=3,
        material=MaterialType.ALUMINUM,
        thickness_nm=200.0,
        description="Bandage/airbridge contact",
        color="#2ECC71",
    ),
    LayerDefinition(
        name="airbridge",
        gds_layer=4,
        material=MaterialType.ALUMINUM,
        thickness_nm=300.0,
        description="Air bridges for crossover connections",
        color="#F39C12",
    ),
    LayerDefinition(
        name="readout",
        gds_layer=5,
        material=MaterialType.ALUMINUM,
        thickness_nm=100.0,
        description="Readout resonator layer",
        color="#9B59B6",
    ),
    LayerDefinition(
        name="etch",
        gds_layer=6,
        material=MaterialType.CUSTOM,
        thickness_nm=0.0,
        description="Etch/subtract helper layer",
        color="#607D8B",
    ),
    LayerDefinition(
        name="marker",
        gds_layer=7,
        material=MaterialType.CUSTOM,
        thickness_nm=0.0,
        description="Marker/alignment/helper layer",
        color="#795548",
    ),
    LayerDefinition(
        name="fake_junction",
        gds_layer=8,
        material=MaterialType.CUSTOM,
        thickness_nm=0.0,
        description="Fake junction / verification marker layer",
        color="#D81B60",
    ),
    LayerDefinition(
        name="text",
        gds_layer=9,
        material=MaterialType.CUSTOM,
        thickness_nm=0.0,
        description="Text/annotation layer",
        color="#455A64",
    ),
    LayerDefinition(
        name="chip_edge",
        gds_layer=10,
        material=MaterialType.CUSTOM,
        thickness_nm=0.0,
        description="Chip edge / boundary layer",
        color="#263238",
    ),
]


class OperationRecord(BaseModel):
    """Single entry in the undo/redo history."""
    operation_id: str = Field(default_factory=_new_uid)
    timestamp: datetime = Field(default_factory=_utcnow)
    operation_type: str
    target_id: str = ""
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    description: str = ""
