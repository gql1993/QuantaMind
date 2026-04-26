"""
Design → GDS/OASIS export.

Converts Design into gdstk geometry with:
  - process-layer mapping profiles
  - hierarchical reusable component cells
  - ground-plane boolean subtraction
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from loguru import logger

from quantamind.server.geometry.component_cell_library import ComponentCellLibrary
from quantamind.server.geometry.generators import generate_component_geometry_result_um
from quantamind.server.geometry.layer_profiles import ProcessLayerProfile, get_process_layer_profile
from quantamind.server.qeda_models.design import Design

M_TO_UM = 1e6


def _rotate_polygon_um(
    pts: list[tuple[float, float]],
    rotation_deg: float,
) -> list[tuple[float, float]]:
    if not rotation_deg:
        return pts
    theta = math.radians(rotation_deg)
    c, s = math.cos(theta), math.sin(theta)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def _build_ground_polys(gdstk, profile: ProcessLayerProfile, chip_w_um: float, chip_h_um: float, subtract_operands: list[Any]) -> list[Any]:
    ground_box = gdstk.rectangle(
        (-chip_w_um / 2, -chip_h_um / 2),
        (chip_w_um / 2, chip_h_um / 2),
        layer=profile.ground_plane,
        datatype=0,
    )
    if not subtract_operands:
        return [ground_box]
    return gdstk.boolean(
        [ground_box],
        subtract_operands,
        "not",
        layer=profile.ground_plane,
        datatype=0,
    )


def _alignment_markers(gdstk, profile: ProcessLayerProfile, chip_w_um: float, chip_h_um: float) -> list[Any]:
    markers = []
    cross_len = min(chip_w_um, chip_h_um) * 0.025
    cross_w = max(20.0, cross_len * 0.12)
    offset_x = chip_w_um / 2 - cross_len * 1.4
    offset_y = chip_h_um / 2 - cross_len * 1.4

    def cross(cx: float, cy: float) -> list[Any]:
        horiz = gdstk.rectangle(
            (cx - cross_len / 2, cy - cross_w / 2),
            (cx + cross_len / 2, cy + cross_w / 2),
            layer=profile.marker,
            datatype=0,
        )
        vert = gdstk.rectangle(
            (cx - cross_w / 2, cy - cross_len / 2),
            (cx + cross_w / 2, cy + cross_len / 2),
            layer=profile.marker,
            datatype=0,
        )
        return [horiz, vert]

    for sx in (-1, 1):
        for sy in (-1, 1):
            markers.extend(cross(sx * offset_x, sy * offset_y))
    markers.extend(cross(0.0, 0.0))
    return markers


def _text_polys(gdstk, profile: ProcessLayerProfile, chip_w_um: float, chip_h_um: float, text: str) -> list[Any]:
    size = max(80.0, min(chip_w_um, chip_h_um) * 0.018)
    origin = (-chip_w_um / 2 + size, chip_h_um / 2 - size * 2.2)
    return gdstk.text(text, size, origin, layer=profile.text, datatype=0)


def _build_export(
    design: Design,
    output_path: Path | str,
    *,
    fmt: str,
    layer_profile: str = "default",
    hierarchical: bool = True,
) -> Path:
    try:
        from quantamind.server.geometry.gdstk_engine import GdstkEngine
    except ImportError:
        raise ImportError(f"gdstk 未安装，无法导出 {fmt.upper()}。请运行: pip install gdstk")

    profile = get_process_layer_profile(layer_profile)
    engine = GdstkEngine(unit=1e-6, precision=1e-9)
    engine._ensure_lib()
    gdstk = engine._gdstk
    top_cell = engine.create_cell(design.name)
    cell_library = ComponentCellLibrary(engine, profile)
    subtract_operands: list[Any] = []

    chip_w_um = max(1000.0, design.metadata.chip_size_x_mm * 1000.0)
    chip_h_um = max(1000.0, design.metadata.chip_size_y_mm * 1000.0)
    chip_edge = gdstk.rectangle(
        (-chip_w_um / 2, -chip_h_um / 2),
        (chip_w_um / 2, chip_h_um / 2),
        layer=profile.chip_edge,
        datatype=0,
    )
    top_cell.add(chip_edge)
    for marker in _alignment_markers(gdstk, profile, chip_w_um, chip_h_um):
        top_cell.add(marker)
    for poly in _text_polys(gdstk, profile, chip_w_um, chip_h_um, design.name):
        top_cell.add(poly)

    for comp in design.components:
        x_um = comp.position_x * M_TO_UM
        y_um = comp.position_y * M_TO_UM
        geometry = generate_component_geometry_result_um(comp)

        if hierarchical:
            cell = cell_library.get_or_create(comp)
            engine.add_reference(
                top_cell,
                cell,
                origin=(x_um, y_um),
                rotation=comp.rotation,
            )
        else:
            for polygon in geometry.polygons:
                poly_um = _rotate_polygon_um(polygon.vertices.tolist(), comp.rotation)
                vertices = [(p[0] + x_um, p[1] + y_um) for p in poly_um]
                engine.add_polygon(
                    top_cell,
                    vertices,
                    layer=profile.map_logical(polygon.layer),
                    datatype=polygon.datatype,
                )

        for cutout_um in geometry.metadata.get("ground_cutouts_um", []):
            poly_um = _rotate_polygon_um(cutout_um, comp.rotation)
            vertices = [(p[0] + x_um, p[1] + y_um) for p in poly_um]
            subtract_operands.append(gdstk.Polygon(vertices, layer=profile.etch, datatype=0))

    for seg in design.routing_segments:
        if not seg.waypoints:
            continue
        spine = [(p[0] * M_TO_UM, p[1] * M_TO_UM) for p in seg.waypoints]
        engine.add_path(
            top_cell,
            spine,
            width=seg.width_um,
            layer=profile.map_logical(seg.layer),
            datatype=0,
        )
        subtract_operands.append(
            gdstk.FlexPath(
                spine,
                seg.width_um + 2 * seg.gap_um,
                layer=profile.etch,
                datatype=0,
            )
        )

    for poly in _build_ground_polys(gdstk, profile, chip_w_um, chip_h_um, subtract_operands):
        top_cell.add(poly)

    output_path = Path(output_path)
    if fmt == "gds":
        engine.export_gds([top_cell], output_path)
    else:
        engine.export_oasis([top_cell], output_path)
    logger.info(
        "{} 导出完成: {} (profile={}, hierarchical={}, component_cells={}, component_families={})",
        fmt.upper(),
        output_path,
        profile.name,
        hierarchical,
        cell_library.size,
        cell_library.family_count,
    )
    return output_path


def design_to_gds(
    design: Design,
    output_path: Path | str,
    *,
    layer_profile: str = "default",
    hierarchical: bool = True,
) -> Path:
    return _build_export(
        design,
        output_path,
        fmt="gds",
        layer_profile=layer_profile,
        hierarchical=hierarchical,
    )


def design_to_oasis(
    design: Design,
    output_path: Path | str,
    *,
    layer_profile: str = "default",
    hierarchical: bool = True,
) -> Path:
    return _build_export(
        design,
        output_path,
        fmt="oas",
        layer_profile=layer_profile,
        hierarchical=hierarchical,
    )
