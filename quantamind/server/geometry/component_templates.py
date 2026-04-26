"""
Normalized parameter templates for common component geometries.
"""

from __future__ import annotations

from typing import Any

from quantamind.server.qeda_models.component import ComponentInstance
from quantamind.server.layout_units import parse_length


def _um(value: Any, default_um: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return parse_length(value) * 1e6
        except Exception:
            return default_um
    return default_um


def classify_component_kind(instance: ComponentInstance, definition_name: str = "") -> str:
    kind = (instance.metadata or {}).get("external_class") or instance.definition_id or definition_name
    key = str(kind).strip().lower()
    if any(token in key for token in ["transmon", "xmon"]):
        return "transmon"
    if any(token in key for token in ["coupledlinetee", "coupled_line_tee"]):
        return "tee"
    if any(token in key for token in ["tunablecoupler", "tunable_coupler", "mytunablecoupler"]):
        return "tunable_coupler"
    if any(token in key for token in ["launchpadwirebond", "launch_pad", "launchpad"]):
        return "launchpad"
    if any(token in key for token in ["connector", "myconnector"]):
        return "connector"
    if any(token in key for token in ["opentoground", "open_to_ground"]):
        return "open_to_ground"
    return "generic"


def normalize_component_template(
    instance: ComponentInstance,
    definition_name: str = "",
) -> dict[str, Any]:
    p = instance.parameters or {}
    kind = classify_component_kind(instance, definition_name)

    normalized: dict[str, Any] = {
        "kind": kind,
        "mirror_x": bool(instance.mirror_x),
        "mirror_y": bool(instance.mirror_y),
    }

    if kind == "transmon":
        raw_connection_pads = p.get("connection_pads", {})
        normalized_pads: dict[str, Any] = {}
        if isinstance(raw_connection_pads, dict):
            for pad_name, pad in raw_connection_pads.items():
                if not isinstance(pad, dict):
                    continue
                normalized_pads[str(pad_name)] = {
                    **pad,
                    "claw_length_um": _um(pad.get("claw_length"), 60.0),
                    "claw_width_um": _um(pad.get("claw_width"), 6.0),
                    "claw_gap_um": _um(pad.get("claw_gap"), 4.0),
                    "ground_spacing_um": _um(pad.get("ground_spacing"), 2.0),
                    "coupling_width_um": _um(pad.get("coupling_width"), 16.0),
                }
        normalized.update(
            {
                "arm_w_um": max(4.0, _um(p.get("cross_width"), 16.0)),
                "north_um": _um(p.get("cross_length1", p.get("cross_length")), 170.0),
                "south_um": _um(p.get("cross_length2", p.get("cross_length")), 162.0),
                "east_um": _um(p.get("cross_length"), 138.0),
                "west_um": _um(p.get("cross_length"), 138.0),
                "center_w_um": max(max(4.0, _um(p.get("cross_width"), 16.0)) * 1.4, 24.0),
                "jj_pad_w_um": _um(p.get("jj_pad_width"), 8.0),
                "jj_pad_h_um": _um(p.get("jj_pad_height"), 6.0),
                "jj_etch_um": _um(p.get("jj_etch_length"), 4.0),
                "connection_pads": normalized_pads,
            }
        )
        return normalized

    if kind == "tee":
        normalized.update(
            {
                "coupling_len_um": _um(p.get("coupling_length"), 280.0),
                "coupling_space_um": _um(p.get("coupling_space"), 3.0),
                "prime_w_um": _um(p.get("prime_width"), 10.0),
                "second_w_um": _um(p.get("second_width"), 10.0),
                "over_len_um": _um(p.get("over_length"), 60.0),
                "down_len_um": _um(p.get("down_length"), 220.0),
            }
        )
        return normalized

    if kind == "tunable_coupler":
        normalized.update(
            {
                "body_w_um": _um(p.get("c_width", p.get("pad_width")), 316.0),
                "body_h_um": max(_um(p.get("a_height"), 30.0) * 2, 18.0),
                "arm_w_um": _um(p.get("l_width"), 9.0),
                "arm_len_um": _um(p.get("cp_arm_length"), 25.5),
                "gap_um": _um(p.get("l_gap"), 16.0),
                "cp_w_um": _um(p.get("cp_width"), 10.0),
                "cp_h_um": _um(p.get("cp_height"), 15.0),
                "cp_len_um": _um(p.get("cp_length"), 10.0),
                "flux_w_um": _um(p.get("fl_width"), 4.0),
                "flux_len_um": _um(p.get("fl_length"), 10.0),
                "a_height_um": _um(p.get("a_height"), 30.0),
            }
        )
        return normalized

    if kind == "launchpad":
        trace_w_um = _um(p.get("trace_width"), 10.0)
        normalized.update(
            {
                "pad_w_um": _um(p.get("pad_width"), 250.0),
                "pad_h_um": _um(p.get("pad_height"), 250.0),
                "pad_gap_um": _um(p.get("pad_gap"), 100.0),
                "lead_len_um": _um(p.get("lead_length"), 176.0),
                "taper_h_um": _um(p.get("taper_height"), 122.0),
                "trace_w_um": trace_w_um,
                "mouth_w_um": max(trace_w_um + 2 * _um(p.get("pad_gap"), 100.0), _um(p.get("pad_width"), 250.0) * 0.55),
            }
        )
        return normalized

    if kind == "connector":
        width_um = _um(p.get("width"), 4.0)
        width0_um = _um(p.get("width0"), 10.0)
        length_um = _um(p.get("length"), 10.0)
        normalized.update(
            {
                "width_um": width_um,
                "width0_um": width0_um,
                "length_um": length_um,
                "wide_len_um": max(length_um * 1.4, 12.0),
                "neck_len_um": max(length_um * 1.8, 18.0),
            }
        )
        return normalized

    if kind == "open_to_ground":
        width_um = _um(p.get("width"), 10.0)
        gap_um = _um(p.get("termination_gap"), 6.0)
        normalized.update(
            {
                "width_um": width_um,
                "gap_um": gap_um,
                "length_um": max(gap_um * 3, 30.0),
            }
        )
        return normalized

    normalized["size_um"] = 120.0
    return normalized

