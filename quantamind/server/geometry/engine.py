"""
Abstract geometry engine interface.

All geometry backends (gdstk, Qiskit Metal, KQCircuits) implement this
interface so that the application and UI layers are decoupled from the
specific backend choice.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np


@dataclass
class Polygon:
    """A 2D polygon represented by ordered vertices (Nx2 float array)."""
    vertices: np.ndarray
    layer: int = 0
    datatype: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.vertices, list):
            self.vertices = np.array(self.vertices, dtype=np.float64)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 2:
            raise ValueError("Vertices must be Nx2 array")

    @property
    def num_points(self) -> int:
        return self.vertices.shape[0]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(min_x, min_y, max_x, max_y)"""
        return (
            float(self.vertices[:, 0].min()),
            float(self.vertices[:, 1].min()),
            float(self.vertices[:, 0].max()),
            float(self.vertices[:, 1].max()),
        )


@dataclass
class PathSegment:
    """A path/trace defined by spine points, width, and layer."""
    spine: np.ndarray
    width: float
    layer: int = 0
    datatype: int = 0
    bend_radius: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.spine, list):
            self.spine = np.array(self.spine, dtype=np.float64)


@dataclass
class CellReference:
    """Reference to another cell (for hierarchical designs)."""
    cell_name: str
    origin: tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    magnification: float = 1.0
    x_reflection: bool = False


@dataclass
class GeometryResult:
    """Result of a geometry generation operation."""
    polygons: list[Polygon] = field(default_factory=list)
    paths: list[PathSegment] = field(default_factory=list)
    references: list[CellReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:
        if not self.polygons:
            return None
        all_bounds = [p.bounds for p in self.polygons]
        return (
            min(b[0] for b in all_bounds),
            min(b[1] for b in all_bounds),
            max(b[2] for b in all_bounds),
            max(b[3] for b in all_bounds),
        )


class AbstractGeometryEngine(ABC):
    """
    Abstract interface for geometry operations.

    Concrete implementations:
      - GdstkEngine (primary, C++ performance)
      - QiskitMetalEngine (Qiskit Metal QGeometry)
      - KQCircuitsEngine (KQCircuits PCell)
    """

    @abstractmethod
    def create_cell(self, name: str) -> Any:
        """Create a new cell/component container."""

    @abstractmethod
    def add_polygon(
        self,
        cell: Any,
        vertices: np.ndarray | Sequence[tuple[float, float]],
        layer: int = 0,
        datatype: int = 0,
    ) -> Any:
        """Add a polygon to a cell."""

    @abstractmethod
    def add_path(
        self,
        cell: Any,
        spine: np.ndarray | Sequence[tuple[float, float]],
        width: float,
        layer: int = 0,
        datatype: int = 0,
        bend_radius: float = 0.0,
    ) -> Any:
        """Add a path/trace to a cell."""

    @abstractmethod
    def add_reference(
        self,
        cell: Any,
        ref_cell: Any,
        origin: tuple[float, float] = (0.0, 0.0),
        rotation: float = 0.0,
        magnification: float = 1.0,
        x_reflection: bool = False,
    ) -> Any:
        """Add a cell reference (hierarchical instantiation)."""

    @abstractmethod
    def boolean_operation(
        self,
        operand_a: list[Any],
        operand_b: list[Any],
        operation: str,
        layer: int = 0,
        datatype: int = 0,
    ) -> list[Any]:
        """
        Perform boolean geometry operation.

        Args:
            operation: One of 'or' (union), 'and' (intersection),
                       'not' (difference), 'xor'.
        """

    @abstractmethod
    def offset(
        self,
        polygons: list[Any],
        distance: float,
        join_type: str = "miter",
        layer: int = 0,
    ) -> list[Any]:
        """Offset (dilate/erode) polygons."""

    @abstractmethod
    def fillet(
        self,
        polygon: Any,
        radius: float,
        max_points: int = 199,
    ) -> Any:
        """Apply fillet (rounding) to polygon corners."""

    @abstractmethod
    def export_gds(self, cells: list[Any], filepath: Path | str, **kwargs: Any) -> Path:
        """Export cells to GDSII file."""

    @abstractmethod
    def export_oasis(self, cells: list[Any], filepath: Path | str, **kwargs: Any) -> Path:
        """Export cells to OASIS file."""

    @abstractmethod
    def get_polygons(self, cell: Any, layer: Optional[int] = None) -> list[Polygon]:
        """Extract all polygons from a cell, optionally filtered by layer."""

    @abstractmethod
    def get_bounding_box(self, cell: Any) -> tuple[float, float, float, float] | None:
        """Get bounding box of a cell: (min_x, min_y, max_x, max_y)."""

    def generate_component(
        self,
        component_type: str,
        parameters: dict[str, Any],
        position: tuple[float, float] = (0.0, 0.0),
        rotation: float = 0.0,
    ) -> GeometryResult:
        """
        Generate geometry for a parameterized component.

        Override in subclass or delegate to component generators.
        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(
            f"Component generation for '{component_type}' not implemented in {type(self).__name__}"
        )
