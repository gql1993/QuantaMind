"""
Route geometry generation for imported CPW/Meander/Pathfinder segments.
"""

from __future__ import annotations

import math
import re
from typing import Any

from quantamind.server.qeda_models.component import ComponentInstance
from quantamind.server.qeda_models.design import RoutingSegment
from quantamind.server.layout_units import parse_length


def _length_m(value: Any, default_m: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        # External bare numeric values are typically millimeters.
        return float(value) * 1e-3
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[-+]?\d+(\.\d+)?", text):
            return float(text) * 1e-3
        try:
            return parse_length(text)
        except Exception:
            return default_m
    return default_m


def _component_size_m(comp: ComponentInstance) -> tuple[float, float]:
    p = comp.parameters or {}
    if "cross_length" in p:
        l = _length_m(p.get("cross_length"), 160e-6)
        return (max(80e-6, l * 1.3), max(80e-6, l * 1.3))
    if "pad_width" in p or "pad_height" in p:
        return (_length_m(p.get("pad_width"), 250e-6), _length_m(p.get("pad_height"), 250e-6))
    if "c_width" in p:
        w = _length_m(p.get("c_width"), 316e-6)
        return (w, max(80e-6, w * 0.35))
    if "coupling_length" in p:
        l = _length_m(p.get("coupling_length"), 200e-6)
        return (max(100e-6, l), max(60e-6, l * 0.3))
    if "width" in p or "height" in p:
        return (_length_m(p.get("width"), 20e-6), _length_m(p.get("height"), 20e-6))
    return (200e-6, 200e-6)


def _rotate(dx: float, dy: float, degrees: float) -> tuple[float, float]:
    theta = math.radians(degrees)
    c = math.cos(theta)
    s = math.sin(theta)
    return (dx * c - dy * s, dx * s + dy * c)


def _unit(vec: tuple[float, float]) -> tuple[float, float]:
    x, y = vec
    n = math.hypot(x, y)
    if n == 0:
        return (1.0, 0.0)
    return (x / n, y / n)


def _turn_left(vec: tuple[float, float]) -> tuple[float, float]:
    x, y = vec
    return (-y, x)


def _turn_right(vec: tuple[float, float]) -> tuple[float, float]:
    x, y = vec
    return (y, -x)


def _pin_local_direction(comp: ComponentInstance, pin_name: str) -> tuple[float, float]:
    params = comp.parameters or {}
    connection_pads = params.get("connection_pads")
    if isinstance(connection_pads, dict) and pin_name in connection_pads:
        pad = connection_pads.get(pin_name)
        if isinstance(pad, dict):
            angle = pad.get("connector_location")
            try:
                deg = float(angle)
                rad = math.radians(deg)
                return (math.cos(rad), math.sin(rad))
            except Exception:
                pass

    pin = pin_name.lower()
    if pin in {"prime_start", "c_pin_l", "port_in"}:
        return (-1.0, 0.0)
    if pin in {"prime_end", "c_pin_r", "port_out"}:
        return (1.0, 0.0)
    if pin in {"second_end", "open"}:
        return (0.0, 1.0)
    if "flux" in pin:
        return (0.0, 1.0)
    if "control" in pin:
        return (0.0, -1.0)
    if pin == "tie":
        return (1.0, 0.0)
    if pin == "bus_01":
        return (0.0, 1.0)
    if pin == "bus_02":
        return (0.0, -1.0)
    return (1.0, 0.0)


def _apply_mirror(vec: tuple[float, float], comp: ComponentInstance) -> tuple[float, float]:
    x, y = vec
    if comp.mirror_x:
        y = -y
    if comp.mirror_y:
        x = -x
    return (x, y)


def component_pin_position(comp: ComponentInstance, pin_name: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Return (pin_position_m, outward_unit_direction_world).
    """
    half_w, half_h = (v / 2 for v in _component_size_m(comp))
    local_dir = _apply_mirror(_pin_local_direction(comp, pin_name), comp)
    dx, dy = _unit(local_dir)

    tx = float("inf") if abs(dx) < 1e-12 else abs(half_w / dx)
    ty = float("inf") if abs(dy) < 1e-12 else abs(half_h / dy)
    t = min(tx, ty)
    local_pos = (dx * t, dy * t)
    world_pos = _rotate(local_pos[0], local_pos[1], comp.rotation)
    world_dir = _unit(_rotate(dx, dy, comp.rotation))
    return ((comp.position_x + world_pos[0], comp.position_y + world_pos[1]), world_dir)


def _polyline_length(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for a, b in zip(points, points[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def _append_manhattan(
    points: list[tuple[float, float]],
    target: tuple[float, float],
    prefer_horizontal: bool = True,
) -> None:
    x0, y0 = points[-1]
    x1, y1 = target
    if abs(x1 - x0) < 1e-12 or abs(y1 - y0) < 1e-12:
        points.append(target)
        return
    if prefer_horizontal:
        points.append((x1, y0))
    else:
        points.append((x0, y1))
    points.append(target)


def _ordered_jogs(raw: Any) -> list[list[Any]]:
    if isinstance(raw, dict):
        items: list[tuple[Any, Any]] = sorted(raw.items(), key=lambda kv: str(kv[0]))
        return [v for _, v in items if isinstance(v, list) and len(v) >= 2]
    return []


def _apply_relative_jogs(
    points: list[tuple[float, float]],
    heading: tuple[float, float],
    jogs: list[list[Any]],
) -> tuple[float, float]:
    current_heading = _unit(heading)
    for spec in jogs:
        turn = str(spec[0]).strip().upper()
        dist = _length_m(spec[1], 0.0)
        if turn == "L":
            current_heading = _unit(_turn_left(current_heading))
        elif turn == "R":
            current_heading = _unit(_turn_right(current_heading))
        elif turn == "U":
            current_heading = (0.0, 1.0)
        elif turn == "D":
            current_heading = (0.0, -1.0)
        p = points[-1]
        points.append((p[0] + current_heading[0] * dist, p[1] + current_heading[1] * dist))
    return current_heading


def _add_meander(
    points: list[tuple[float, float]],
    target: tuple[float, float],
    target_length_m: float,
    spacing_m: float,
) -> None:
    base_start = points[-1]
    direct = abs(target[0] - base_start[0]) + abs(target[1] - base_start[1])
    need_extra = target_length_m - (_polyline_length(points) + direct)
    if need_extra <= max(2 * spacing_m, 100e-6):
        _append_manhattan(points, target, prefer_horizontal=True)
        return

    spacing_m = max(spacing_m, 50e-6)
    dx = target[0] - base_start[0]
    dy = target[1] - base_start[1]
    horizontal = abs(dx) >= abs(dy)
    sign_main = 1.0 if (dx if horizontal else dy) >= 0 else -1.0
    amp_sign = 1.0 if (dy if horizontal else dx) >= 0 else -1.0
    amplitude = max(spacing_m * 2, 150e-6)
    loop_extra = 4 * amplitude
    loops = max(1, min(64, int(round(need_extra / max(loop_extra, 1e-12)))))

    if horizontal:
        step = dx / (loops * 2 + 2) if loops > 0 else dx / 2
        x, y = base_start
        for i in range(loops):
            x += step
            points.append((x, y))
            y += amp_sign * amplitude if i % 2 == 0 else -amp_sign * amplitude
            points.append((x, y))
            x += step
            points.append((x, y))
        _append_manhattan(points, target, prefer_horizontal=False)
    else:
        step = dy / (loops * 2 + 2) if loops > 0 else dy / 2
        x, y = base_start
        for i in range(loops):
            y += step
            points.append((x, y))
            x += amp_sign * amplitude if i % 2 == 0 else -amp_sign * amplitude
            points.append((x, y))
            y += step
            points.append((x, y))
        _append_manhattan(points, target, prefer_horizontal=True)


def build_route_waypoints(
    segment: RoutingSegment,
    source: ComponentInstance,
    target: ComponentInstance,
) -> list[tuple[float, float]]:
    """
    Build a polyline in meters from segment metadata.
    """
    meta = segment.metadata or {}
    cfg = meta.get("external_config", {}) if isinstance(meta.get("external_config"), dict) else {}
    lead = cfg.get("lead", {}) if isinstance(cfg.get("lead"), dict) else {}
    meander = cfg.get("meander", {}) if isinstance(cfg.get("meander"), dict) else {}
    route_class = str(meta.get("external_class", "") or meta.get("route_class", "")).lower()

    start_pin, start_dir = component_pin_position(source, segment.source_port)
    end_pin, end_dir = component_pin_position(target, segment.target_port)
    end_dir = (-end_dir[0], -end_dir[1])

    start_straight = _length_m(lead.get("start_straight", 0.0), 0.0)
    end_straight = _length_m(lead.get("end_straight", 0.0), 0.0)
    start_point = (
        start_pin[0] + start_dir[0] * start_straight,
        start_pin[1] + start_dir[1] * start_straight,
    )
    end_point = (
        end_pin[0] + end_dir[0] * end_straight,
        end_pin[1] + end_dir[1] * end_straight,
    )

    points = [start_pin, start_point]
    heading = start_dir
    heading = _apply_relative_jogs(points, heading, _ordered_jogs(lead.get("start_jogged_extension")))

    total_length_m = _length_m(cfg.get("total_length", 0.0), 0.0)
    spacing_value = meander.get("spacing", 0.0)
    spacing_m = _length_m(spacing_value, 0.1e-3 if isinstance(spacing_value, (int, float)) else 0.0)

    if "meander" in route_class or total_length_m > 0.0:
        _add_meander(points, end_point, total_length_m, spacing_m)
    else:
        _append_manhattan(
            points,
            end_point,
            prefer_horizontal=abs(end_point[0] - points[-1][0]) >= abs(end_point[1] - points[-1][1]),
        )

    _apply_relative_jogs(points, heading, _ordered_jogs(lead.get("end_jogged_extension")))
    points.append(end_pin)

    cleaned: list[tuple[float, float]] = []
    for pt in points:
        if cleaned and math.isclose(cleaned[-1][0], pt[0], abs_tol=1e-12) and math.isclose(cleaned[-1][1], pt[1], abs_tol=1e-12):
            continue
        cleaned.append(pt)
    return cleaned

