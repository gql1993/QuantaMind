"""
Import external (Qiskit Metal style) design JSON into Q-EDA Design.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from quantamind.server.services.layout_script_parser import (
    LayoutInstanceSpec,
    find_companion_layout,
    parse_layout_script,
)
from quantamind.server.geometry.routing_geometry import build_route_waypoints
from quantamind.server.qeda_models.component import ComponentInstance
from quantamind.server.qeda_models.design import Design, RoutingSegment
from quantamind.server.qeda_models.topology import Topology
from quantamind.server.layout_units import parse_length


def is_external_design_payload(data: Any) -> bool:
    """Heuristic check for external design dictionary."""
    if not isinstance(data, dict) or not data:
        return False
    if "design_id" in data and "components" in data:
        return False
    first = next(iter(data.values()))
    return isinstance(first, dict) and ("pin_inputs" in first or "pos_x" in first)


def _safe_to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_parse_length_m(value: Any, default_m: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        # External bare numeric values in these projects are typically millimeters.
        return float(value) * 1e-3
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[-+]?\d+(\.\d+)?", text):
            return float(text) * 1e-3
        try:
            return parse_length(text)
        except Exception:
            # Unknown variables like "cpw_width" are preserved in parameters.
            return default_m
    return default_m


def _guess_definition_id(name: str) -> str:
    n = name.lower()
    if n.startswith("q") and len(n) > 1 and n[1:].isdigit():
        return "xmon_transmon"
    if n.startswith("tq"):
        return "coupled_line_tee"
    if n.startswith("tunable_coupler"):
        return "tunable_coupler"
    if n.startswith("launchpad") or "launch" in n:
        return "launch_pad"
    if n.startswith("connector"):
        return "connector"
    if n.startswith("otg"):
        return "open_to_ground"
    return "custom"


def _normalize_definition_id(class_name: str, fallback_name: str) -> str:
    if not class_name:
        return _guess_definition_id(fallback_name)
    return class_name.strip().lower()


def _infer_route_class(cfg: dict[str, Any]) -> str:
    if not isinstance(cfg, dict):
        return "RouteStraight"
    if isinstance(cfg.get("meander"), dict) or cfg.get("total_length"):
        return "RouteMeander"
    lead = cfg.get("lead")
    if isinstance(lead, dict):
        if lead.get("start_jogged_extension") or lead.get("end_jogged_extension"):
            return "RoutePathfinder"
    if isinstance(cfg.get("anchors"), dict) and cfg.get("anchors"):
        return "RoutePathfinder"
    return "RouteStraight"


def import_external_design_dict(
    payload: dict[str, Any],
    design_name: str = "Imported External Design",
    layout_specs: dict[str, LayoutInstanceSpec] | None = None,
) -> tuple[Design, dict[str, Any]]:
    """
    Convert external JSON dict into Q-EDA design.

    Returns (design, report) where report contains conversion stats/warnings.
    """
    design = Design(name=design_name, topology=Topology(name=f"{design_name}_topo"))
    name_to_instance_id: dict[str, str] = {}
    instance_by_id: dict[str, ComponentInstance] = {}
    warnings: list[str] = []

    component_count = 0
    route_count = 0
    skipped_routes = 0
    max_abs_x = 0.0
    max_abs_y = 0.0

    # 1) Components
    for name, cfg in payload.items():
        if not isinstance(cfg, dict):
            continue
        if "pin_inputs" in cfg:
            continue

        pos_x = _safe_parse_length_m(cfg.get("pos_x", 0.0), 0.0)
        pos_y = _safe_parse_length_m(cfg.get("pos_y", 0.0), 0.0)
        rotation = _safe_to_float(cfg.get("orientation", 0.0), 0.0)

        params = dict(cfg)
        params.pop("pos_x", None)
        params.pop("pos_y", None)
        params.pop("orientation", None)
        layout_spec = (layout_specs or {}).get(name)
        if layout_spec is not None and layout_spec.options:
            params["_layout_options"] = layout_spec.options

        comp = ComponentInstance(
            definition_id=_normalize_definition_id(
                layout_spec.class_name if layout_spec is not None else "",
                name,
            ),
            name=name,
            position_x=pos_x,
            position_y=pos_y,
            rotation=rotation,
            parameters=params,
            metadata={
                "external_name": name,
                "external_class": layout_spec.class_name if layout_spec is not None else "",
                "layout_variable_name": layout_spec.variable_name if layout_spec is not None else "",
            },
        )
        design.add_component(comp)
        name_to_instance_id[name] = comp.instance_id
        instance_by_id[comp.instance_id] = comp
        component_count += 1
        max_abs_x = max(max_abs_x, abs(pos_x))
        max_abs_y = max(max_abs_y, abs(pos_y))

    # 2) Routes
    for name, cfg in payload.items():
        if not isinstance(cfg, dict):
            continue
        pin_inputs = cfg.get("pin_inputs")
        if not isinstance(pin_inputs, dict):
            continue

        start = pin_inputs.get("start_pin", {}) if isinstance(pin_inputs.get("start_pin"), dict) else {}
        end = pin_inputs.get("end_pin", {}) if isinstance(pin_inputs.get("end_pin"), dict) else {}
        s_name = start.get("component")
        t_name = end.get("component")
        s_port = str(start.get("pin", "start"))
        t_port = str(end.get("pin", "end"))
        if not s_name or not t_name:
            skipped_routes += 1
            warnings.append(f"{name}: missing start/end component")
            continue
        s_id = name_to_instance_id.get(str(s_name))
        t_id = name_to_instance_id.get(str(t_name))
        if not s_id or not t_id:
            skipped_routes += 1
            warnings.append(f"{name}: unresolved endpoint ({s_name} -> {t_name})")
            continue

        width_um = _safe_parse_length_m(cfg.get("trace_width", "10um"), 10e-6) * 1e6
        gap_um = _safe_parse_length_m(cfg.get("trace_gap", "6um"), 6e-6) * 1e6
        try:
            layer = int(cfg.get("layer", 1))
        except Exception:
            layer = 1

        layout_spec = (layout_specs or {}).get(name)
        s_comp = instance_by_id.get(s_id)
        t_comp = instance_by_id.get(t_id)
        waypoints: list[tuple[float, float]] = []
        route_class = (
            layout_spec.class_name
            if layout_spec is not None and layout_spec.class_name
            else _infer_route_class(cfg)
        )

        route = RoutingSegment(
            source_instance_id=s_id,
            source_port=s_port,
            target_instance_id=t_id,
            target_port=t_port,
            waypoints=waypoints,
            layer=layer,
            width_um=width_um,
            gap_um=gap_um,
            routing_type=route_class,
            metadata={
                "external_name": name,
                "external_class": route_class,
                "layout_variable_name": layout_spec.variable_name if layout_spec is not None else "",
                "external_config": cfg,
                "layout_options": layout_spec.options if layout_spec is not None else {},
                "route_class": route_class,
            },
        )
        if s_comp is not None and t_comp is not None:
            route.waypoints = build_route_waypoints(route, s_comp, t_comp)
        design.add_routing(route)
        route_count += 1

    report = {
        "component_count": component_count,
        "route_count": route_count,
        "skipped_routes": skipped_routes,
        "warnings": warnings[:50],
    }
    # Infer chip size from imported placement envelope with 10% margin.
    design.metadata.chip_size_x_mm = max(
        design.metadata.chip_size_x_mm, (2.2 * max_abs_x * 1e3) if max_abs_x > 0 else 10.0
    )
    design.metadata.chip_size_y_mm = max(
        design.metadata.chip_size_y_mm, (2.2 * max_abs_y * 1e3) if max_abs_y > 0 else 10.0
    )
    design.project_config["external_import_report"] = report
    design.project_config["external_import_format"] = "qiskit_metal_json"
    if layout_specs is not None:
        design.project_config["layout_spec_count"] = len(layout_specs)
    return design, report


def import_external_design_file(path: Path | str) -> tuple[Design, dict[str, Any]]:
    import json

    p = Path(path)
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("External design JSON must be an object")
    layout_path = find_companion_layout(p)
    layout_specs = parse_layout_script(layout_path) if layout_path else None
    design, report = import_external_design_dict(
        data,
        design_name=p.stem,
        layout_specs=layout_specs,
    )
    report["layout_path"] = str(layout_path) if layout_path else ""
    report["layout_spec_count"] = len(layout_specs or {})
    return design, report

