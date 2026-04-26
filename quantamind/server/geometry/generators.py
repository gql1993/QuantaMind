"""
Component geometry generators.

Generate more realistic local geometries (in um) for common quantum-chip parts.
These geometries are shared by the canvas and GDS export paths.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from quantamind.server.geometry.component_templates import normalize_component_template
from quantamind.server.geometry.engine import GeometryResult, Polygon
from quantamind.server.geometry.geometry_cache import get_geometry_cache
from quantamind.server.qeda_models.component import ComponentInstance

if TYPE_CHECKING:
    from quantamind.server.qeda_models.component import ComponentDefinition


def _rect(width_um: float, height_um: float) -> list[tuple[float, float]]:
    half_w = width_um / 2
    half_h = height_um / 2
    return [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
    ]


def _translate_polygon(
    polygon_um: list[tuple[float, float]],
    dx_um: float,
    dy_um: float,
) -> list[tuple[float, float]]:
    return [(x + dx_um, y + dy_um) for x, y in polygon_um]


def _rotate_polygon(
    polygon_um: list[tuple[float, float]],
    degrees: float,
) -> list[tuple[float, float]]:
    if not degrees:
        return list(polygon_um)
    theta = math.radians(degrees)
    c = math.cos(theta)
    s = math.sin(theta)
    return [(x * c - y * s, x * s + y * c) for x, y in polygon_um]


def _mirror_polygon(
    polygon_um: list[tuple[float, float]],
    mirror_x: bool = False,
    mirror_y: bool = False,
) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for x, y in polygon_um:
        out.append(((-x if mirror_y else x), (-y if mirror_x else y)))
    return out


def _mirror_geometry(result: GeometryResult, mirror_x: bool, mirror_y: bool) -> GeometryResult:
    mirrored_metadata = dict(result.metadata)
    if "ground_cutouts_um" in mirrored_metadata:
        mirrored_metadata["ground_cutouts_um"] = [
            _mirror_polygon(poly, mirror_x=mirror_x, mirror_y=mirror_y)
            for poly in mirrored_metadata["ground_cutouts_um"]
        ]
    mirrored = GeometryResult(metadata=mirrored_metadata)
    for poly in result.polygons:
        mirrored.polygons.append(
            Polygon(
                vertices=_mirror_polygon(poly.vertices.tolist(), mirror_x=mirror_x, mirror_y=mirror_y),
                layer=poly.layer,
                datatype=poly.datatype,
            )
        )
    return mirrored


def _claw_polygon(
    claw_length_um: float,
    claw_width_um: float,
    claw_gap_um: float,
    stem_width_um: float,
) -> list[tuple[float, float]]:
    outer_w = max(stem_width_um, 2 * claw_width_um + claw_gap_um)
    inner_half = claw_gap_um / 2
    outer_half = outer_w / 2
    top = claw_length_um
    stem_bottom = -max(claw_width_um * 1.8, 8.0)
    return [
        (-outer_half, stem_bottom),
        (outer_half, stem_bottom),
        (outer_half, 0.0),
        (inner_half + claw_width_um, 0.0),
        (inner_half + claw_width_um, top),
        (inner_half, top),
        (inner_half, claw_width_um),
        (-inner_half, claw_width_um),
        (-inner_half, top),
        (-inner_half - claw_width_um, top),
        (-inner_half - claw_width_um, 0.0),
        (-outer_half, 0.0),
    ]


def _result_from_layered_polygons(
    layer_to_polygons: list[tuple[int, list[tuple[float, float]]]],
    metadata: dict[str, Any] | None = None,
) -> GeometryResult:
    result = GeometryResult(metadata=metadata or {})
    for layer, polygon in layer_to_polygons:
        result.polygons.append(Polygon(vertices=polygon, layer=layer))
    return result


def _build_transmon_geometry(normalized: dict[str, Any]) -> GeometryResult:
    arm_w = normalized["arm_w_um"]
    north = normalized["north_um"]
    south = normalized["south_um"]
    east = normalized["east_um"]
    west = normalized["west_um"]
    jj_pad_w = normalized["jj_pad_w_um"]
    jj_pad_h = normalized["jj_pad_h_um"]
    jj_etch = normalized["jj_etch_um"]
    center_half = normalized["center_w_um"] / 2

    main_island = [
        (-arm_w / 2, -south),
        (arm_w / 2, -south),
        (arm_w / 2, -center_half),
        (east, -center_half),
        (east, center_half),
        (arm_w / 2, center_half),
        (arm_w / 2, north),
        (-arm_w / 2, north),
        (-arm_w / 2, center_half),
        (-west, center_half),
        (-west, -center_half),
        (-arm_w / 2, -center_half),
    ]
    layered: list[tuple[int, list[tuple[float, float]]]] = [(1, main_island)]
    ground_cutouts: list[list[tuple[float, float]]] = []

    connection_pads = normalized.get("connection_pads")
    if isinstance(connection_pads, dict):
        for pad in connection_pads.values():
            if not isinstance(pad, dict):
                continue
            claw_length = float(pad.get("claw_length_um", 60.0))
            claw_width = float(pad.get("claw_width_um", 6.0))
            claw_gap = float(pad.get("claw_gap_um", 4.0))
            coupling_width = float(pad.get("coupling_width_um", arm_w))
            connector_location = float(pad.get("connector_location", 90))
            base_gap = float(pad.get("ground_spacing_um", 2.0)) + 4.0
            claw = _claw_polygon(claw_length, claw_width, claw_gap, coupling_width)
            claw = _translate_polygon(claw, 0.0, center_half + base_gap)
            claw = _rotate_polygon(claw, connector_location - 90.0)
            layered.append((1, claw))
            claw_gap_poly = _translate_polygon(
                _rect(claw_gap, max(claw_length * 0.82, claw_width * 2)),
                0.0,
                center_half + base_gap + claw_length * 0.48,
            )
            claw_gap_poly = _rotate_polygon(claw_gap_poly, connector_location - 90.0)
            ground_cutouts.append(claw_gap_poly)

    bottom_y = -center_half - jj_pad_h / 2 - jj_etch / 2
    left_pad = _translate_polygon(_rect(jj_pad_w, jj_pad_h), -jj_pad_w * 0.6, bottom_y)
    right_pad = _translate_polygon(_rect(jj_pad_w, jj_pad_h), jj_pad_w * 0.6, bottom_y)
    bridge_w = max(jj_etch * 0.7, 1.5)
    bridge_h = max(jj_etch * 0.6, 1.0)
    bridge = _translate_polygon(_rect(bridge_w, bridge_h), 0.0, -center_half - jj_etch * 0.55)
    etch = _translate_polygon(
        _rect(jj_pad_w * 2.1, max(jj_etch * 1.4, jj_pad_h * 0.9)),
        0.0,
        -center_half - jj_etch * 0.55,
    )
    fake_junction = _translate_polygon(
        _rect(max(bridge_w * 1.2, 2.0), max(bridge_h * 1.2, 2.0)),
        0.0,
        -center_half - jj_etch * 0.55,
    )
    layered.extend([(2, left_pad), (2, right_pad), (2, bridge), (6, etch), (8, fake_junction)])
    return _result_from_layered_polygons(
        layered,
        {"kind": "transmon", "ground_cutouts_um": ground_cutouts},
    )


def _build_tee_geometry(normalized: dict[str, Any]) -> GeometryResult:
    coupling_len = normalized["coupling_len_um"]
    coupling_space = normalized["coupling_space_um"]
    prime_w = normalized["prime_w_um"]
    second_w = normalized["second_w_um"]
    over_len = normalized["over_len_um"]
    down_len = normalized["down_len_um"]
    horizontal = _translate_polygon(
        _rect(coupling_len + 2 * over_len, prime_w),
        0.0,
        prime_w / 2 + coupling_space + second_w / 2,
    )
    vertical = _translate_polygon(_rect(second_w, down_len + second_w), 0.0, -down_len / 2)
    coupling_region = _translate_polygon(
        _rect(max(coupling_len * 0.42, second_w * 2.5), max(prime_w + coupling_space * 2, second_w * 1.8)),
        0.0,
        prime_w / 2 + coupling_space + second_w / 2 - prime_w * 0.1,
    )
    coupling_gap = _translate_polygon(
        _rect(max(coupling_len * 0.34, second_w * 1.6), max(coupling_space * 1.3, 2.0)),
        0.0,
        prime_w / 2 + second_w / 2,
    )
    return _result_from_layered_polygons(
        [(1, horizontal), (1, vertical), (1, coupling_region)],
        {"kind": "tee", "ground_cutouts_um": [coupling_gap]},
    )


def _build_tunable_coupler_geometry(normalized: dict[str, Any]) -> GeometryResult:
    body = _rect(normalized["body_w_um"], normalized["body_h_um"])
    top_stem = _translate_polygon(
        _rect(normalized["cp_w_um"], normalized["cp_h_um"] * 2 + normalized["cp_len_um"]),
        0.0,
        normalized["a_height_um"] + (normalized["cp_h_um"] * 2 + normalized["cp_len_um"]) / 2,
    )
    left_arm = _translate_polygon(
        _rect(normalized["arm_len_um"], normalized["arm_w_um"]),
        -(normalized["body_w_um"] + normalized["arm_len_um"]) / 2 + 10.0,
        0.0,
    )
    right_arm = _translate_polygon(
        _rect(normalized["arm_len_um"], normalized["arm_w_um"]),
        (normalized["body_w_um"] + normalized["arm_len_um"]) / 2 - 10.0,
        0.0,
    )
    gap_poly = _rect(max(normalized["cp_w_um"] * 0.45, 3.0), max(normalized["gap_um"], 10.0))
    flux_stub = _translate_polygon(
        _rect(normalized["flux_w_um"], normalized["flux_len_um"] + normalized["a_height_um"] * 0.8),
        0.0,
        -(normalized["flux_len_um"] + normalized["a_height_um"] * 0.8) / 2 - normalized["a_height_um"],
    )
    return _result_from_layered_polygons(
        [(1, body), (1, top_stem), (1, left_arm), (1, right_arm), (1, flux_stub)],
        {"kind": "tunable_coupler", "ground_cutouts_um": [gap_poly]},
    )


def _build_launchpad_geometry(normalized: dict[str, Any]) -> GeometryResult:
    pad = _rect(normalized["pad_w_um"], normalized["pad_h_um"])
    top = normalized["pad_h_um"] / 2
    taper = [
        (-normalized["mouth_w_um"] / 2, top),
        (normalized["mouth_w_um"] / 2, top),
        (normalized["trace_w_um"] / 2, top + normalized["taper_h_um"]),
        (-normalized["trace_w_um"] / 2, top + normalized["taper_h_um"]),
    ]
    lead = _translate_polygon(
        _rect(normalized["trace_w_um"], normalized["lead_len_um"]),
        0.0,
        top + normalized["taper_h_um"] + normalized["lead_len_um"] / 2,
    )
    cutout = _translate_polygon(
        _rect(
            max(normalized["mouth_w_um"] - normalized["trace_w_um"], 2.0),
            max(normalized["pad_gap_um"], 2.0),
        ),
        0.0,
        top + normalized["pad_gap_um"] * 0.25,
    )
    return _result_from_layered_polygons(
        [(1, pad), (1, taper), (1, lead)],
        {"kind": "launchpad", "ground_cutouts_um": [cutout]},
    )


def _build_connector_geometry(normalized: dict[str, Any]) -> GeometryResult:
    landing = _translate_polygon(
        _rect(normalized["width0_um"], normalized["wide_len_um"]),
        0.0,
        -normalized["neck_len_um"] / 2,
    )
    taper = [
        (-normalized["width0_um"] / 2, -normalized["neck_len_um"] / 2),
        (normalized["width0_um"] / 2, -normalized["neck_len_um"] / 2),
        (normalized["width_um"] / 2, 0.0),
        (-normalized["width_um"] / 2, 0.0),
    ]
    neck = _translate_polygon(_rect(normalized["width_um"], normalized["neck_len_um"]), 0.0, normalized["neck_len_um"] / 2)
    return _result_from_layered_polygons([(1, landing), (1, taper), (1, neck)], {"kind": "connector"})


def _build_open_to_ground_geometry(normalized: dict[str, Any]) -> GeometryResult:
    head = _translate_polygon(_rect(normalized["width_um"], normalized["width_um"]), 0.0, -normalized["length_um"] / 3)
    stem = _translate_polygon(_rect(max(normalized["width_um"] * 0.45, 2.0), normalized["length_um"]), 0.0, normalized["length_um"] / 6)
    return _result_from_layered_polygons([(1, head), (1, stem)], {"kind": "open_to_ground"})


def _build_generic_geometry(normalized: dict[str, Any]) -> GeometryResult:
    size_um = float(normalized.get("size_um", 120.0))
    return _result_from_layered_polygons([(1, _rect(size_um, size_um))], {"kind": "generic"})


def _build_local_geometry_um(normalized: dict[str, Any]) -> GeometryResult:
    kind = normalized["kind"]
    if kind == "transmon":
        return _build_transmon_geometry(normalized)
    if kind == "tee":
        return _build_tee_geometry(normalized)
    if kind == "tunable_coupler":
        return _build_tunable_coupler_geometry(normalized)
    if kind == "launchpad":
        return _build_launchpad_geometry(normalized)
    if kind == "connector":
        return _build_connector_geometry(normalized)
    if kind == "open_to_ground":
        return _build_open_to_ground_geometry(normalized)
    return _build_generic_geometry(normalized)


def generate_component_geometry_result_um(
    instance: ComponentInstance,
    definition: "ComponentDefinition | None" = None,
) -> GeometryResult:
    """
    Generate local component geometry in um centered near origin.

    Rotation is applied by the canvas/export path; mirror is applied here.
    """
    normalized = normalize_component_template(
        instance,
        definition.name if definition is not None else "",
    )
    cache = get_geometry_cache()
    cache_key = cache.key_for(
        {
            "component_geometry_um": {
                k: v for k, v in normalized.items() if k not in {"mirror_x", "mirror_y"}
            }
        }
    )
    cached = cache.get(cache_key)
    if cached is None:
        cached = cache.set(cache_key, _build_local_geometry_um(normalized))
    return _mirror_geometry(cached, normalized["mirror_x"], normalized["mirror_y"])


def generate_component_polygons_um(
    instance: ComponentInstance,
    definition: "ComponentDefinition | None" = None,
) -> list[list[tuple[float, float]]]:
    """Generate local component polygons in um for display/export."""
    geometry = generate_component_geometry_result_um(instance, definition)
    return [poly.vertices.tolist() for poly in geometry.polygons]


def generate_component_polygon_um(
    instance: ComponentInstance,
    definition: "ComponentDefinition | None" = None,
) -> list[tuple[float, float]]:
    """Backward-compatible single-polygon accessor."""
    return generate_component_polygons_um(instance, definition)[0]


def generate_component_geometry(
    instance: ComponentInstance,
    definition: "ComponentDefinition | None" = None,
    engine=None,
) -> list[tuple[float, float]]:
    """Backward-compatible geometry entrypoint."""
    return generate_component_polygon_um(instance, definition)
