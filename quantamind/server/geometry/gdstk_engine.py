"""
gdstk-based geometry engine implementation.

gdstk is a high-performance C++ library for GDSII/OASIS manipulation,
chosen as the primary backend for Q-EDA per the V7 architecture specification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np
from loguru import logger

from quantamind.server.geometry.engine import AbstractGeometryEngine, Polygon


class GdstkEngine(AbstractGeometryEngine):
    """
    Geometry engine backed by gdstk.

    Lazy-imports gdstk to allow the framework to load even when
    gdstk is not installed (e.g., during testing of other layers).
    """

    def __init__(self, precision: float = 1e-9, unit: float = 1e-6) -> None:
        self._precision = precision
        self._unit = unit
        self._lib: Any = None
        self._gdstk: Any = None

    def _ensure_lib(self) -> Any:
        if self._gdstk is None:
            try:
                import gdstk
                self._gdstk = gdstk
            except ImportError:
                raise ImportError(
                    "gdstk is required for GdstkEngine. Install with: pip install gdstk"
                )
        if self._lib is None:
            self._lib = self._gdstk.Library(
                name="qeda_library",
                unit=self._unit,
                precision=self._precision,
            )
        return self._lib

    def create_cell(self, name: str) -> Any:
        lib = self._ensure_lib()
        cell = lib.new_cell(name)
        logger.debug("Created cell: {}", name)
        return cell

    def add_polygon(
        self,
        cell: Any,
        vertices: np.ndarray | Sequence[tuple[float, float]],
        layer: int = 0,
        datatype: int = 0,
    ) -> Any:
        gdstk = self._gdstk
        if isinstance(vertices, np.ndarray):
            vertices = vertices.tolist()
        poly = gdstk.Polygon(vertices, layer=layer, datatype=datatype)
        cell.add(poly)
        return poly

    def add_path(
        self,
        cell: Any,
        spine: np.ndarray | Sequence[tuple[float, float]],
        width: float,
        layer: int = 0,
        datatype: int = 0,
        bend_radius: float = 0.0,
    ) -> Any:
        gdstk = self._gdstk
        if isinstance(spine, np.ndarray):
            spine = spine.tolist()
        if bend_radius > 0:
            path = gdstk.FlexPath(
                spine, width, layer=layer, datatype=datatype, bend_radius=bend_radius
            )
        else:
            path = gdstk.FlexPath(spine, width, layer=layer, datatype=datatype)
        cell.add(path)
        return path

    def add_reference(
        self,
        cell: Any,
        ref_cell: Any,
        origin: tuple[float, float] = (0.0, 0.0),
        rotation: float = 0.0,
        magnification: float = 1.0,
        x_reflection: bool = False,
    ) -> Any:
        gdstk = self._gdstk
        ref = gdstk.Reference(
            ref_cell,
            origin=origin,
            rotation=np.radians(rotation),
            magnification=magnification,
            x_reflection=x_reflection,
        )
        cell.add(ref)
        return ref

    def boolean_operation(
        self,
        operand_a: list[Any],
        operand_b: list[Any],
        operation: str,
        layer: int = 0,
        datatype: int = 0,
    ) -> list[Any]:
        gdstk = self._gdstk
        return gdstk.boolean(
            operand_a, operand_b, operation, layer=layer, datatype=datatype
        )

    def offset(
        self,
        polygons: list[Any],
        distance: float,
        join_type: str = "miter",
        layer: int = 0,
    ) -> list[Any]:
        gdstk = self._gdstk
        return gdstk.offset(polygons, distance, join=join_type, layer=layer)

    def fillet(self, polygon: Any, radius: float, max_points: int = 199) -> Any:
        polygon.fillet(radius, max_points=max_points)
        return polygon

    def export_gds(self, cells: list[Any], filepath: Path | str, **kwargs: Any) -> Path:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        lib = self._ensure_lib()
        lib.write_gds(str(filepath), **kwargs)
        logger.info("Exported GDS to {}", filepath)
        return filepath

    def export_oasis(self, cells: list[Any], filepath: Path | str, **kwargs: Any) -> Path:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        lib = self._ensure_lib()
        lib.write_oas(str(filepath), **kwargs)
        logger.info("Exported OASIS to {}", filepath)
        return filepath

    def get_polygons(self, cell: Any, layer: Optional[int] = None) -> list[Polygon]:
        results: list[Polygon] = []
        for poly in cell.polygons:
            if layer is not None and poly.layer != layer:
                continue
            results.append(
                Polygon(
                    vertices=np.array(poly.points),
                    layer=poly.layer,
                    datatype=poly.datatype,
                )
            )
        return results

    def get_bounding_box(self, cell: Any) -> tuple[float, float, float, float] | None:
        bb = cell.bounding_box()
        if bb is None:
            return None
        return (bb[0][0], bb[0][1], bb[1][0], bb[1][1])
