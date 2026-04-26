"""
Semantic component cell template library for hierarchical GDS export.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from quantamind.server.geometry.component_templates import normalize_component_template
from quantamind.server.geometry.generators import generate_component_geometry_result_um
from quantamind.server.geometry.layer_profiles import ProcessLayerProfile
from quantamind.server.qeda_models.component import ComponentInstance


@dataclass(frozen=True)
class ComponentTemplateKey:
    family: str
    variant: str
    digest: str

    @property
    def cell_name(self) -> str:
        return f"tpl_{self.family}_{self.variant}_{self.digest[:8]}"


@dataclass(frozen=True)
class ComponentFamilyKey:
    family: str
    variant: str

    @property
    def family_name(self) -> str:
        return f"fam_{self.family}_{self.variant}"


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {str(k): _rounded(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_rounded(v) for v in value]
    return value


def _bucket(value: float, step: float) -> int:
    return int(round(value / step) * step)


def _variant_from_template(normalized: dict[str, Any]) -> str:
    kind = normalized["kind"]
    if kind == "transmon":
        return f"cw{_bucket(normalized['arm_w_um'], 4)}_jj{_bucket(normalized['jj_pad_w_um'], 2)}_pads{len(normalized.get('connection_pads', {}))}"
    if kind == "tee":
        return f"cl{_bucket(normalized['coupling_len_um'], 20)}_pw{_bucket(normalized['prime_w_um'], 2)}"
    if kind == "tunable_coupler":
        return f"bw{_bucket(normalized['body_w_um'], 20)}_gap{_bucket(normalized['gap_um'], 2)}"
    if kind == "launchpad":
        return f"pw{_bucket(normalized['pad_w_um'], 10)}_tw{_bucket(normalized['trace_w_um'], 2)}"
    if kind == "connector":
        return f"w{_bucket(normalized['width_um'], 2)}_w0{_bucket(normalized['width0_um'], 2)}"
    if kind == "open_to_ground":
        return f"w{_bucket(normalized['width_um'], 2)}_g{_bucket(normalized['gap_um'], 2)}"
    return "generic"


def build_component_template_key(
    instance: ComponentInstance,
    definition_name: str = "",
) -> ComponentTemplateKey:
    normalized = normalize_component_template(instance, definition_name)
    payload = {
        k: v
        for k, v in normalized.items()
        if k not in {"mirror_x", "mirror_y"}
    }
    digest = hashlib.sha1(
        json.dumps(_rounded(payload), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return ComponentTemplateKey(
        family=normalized["kind"],
        variant=_variant_from_template(normalized),
        digest=digest,
    )


def build_component_family_key(
    instance: ComponentInstance,
    definition_name: str = "",
) -> ComponentFamilyKey:
    normalized = normalize_component_template(instance, definition_name)
    return ComponentFamilyKey(
        family=normalized["kind"],
        variant=_variant_from_template(normalized),
    )


class ComponentCellLibrary:
    """
    Reusable semantic template-cell library for hierarchical export.
    """

    def __init__(self, engine: Any, profile: ProcessLayerProfile) -> None:
        self._engine = engine
        self._profile = profile
        self._cells: dict[ComponentTemplateKey, Any] = {}
        self._family_counts: dict[ComponentFamilyKey, int] = {}

    def get_or_create(self, instance: ComponentInstance, definition_name: str = "") -> Any:
        key = build_component_template_key(instance, definition_name)
        family_key = build_component_family_key(instance, definition_name)
        self._family_counts[family_key] = self._family_counts.get(family_key, 0) + 1
        if key in self._cells:
            return self._cells[key]

        geometry = generate_component_geometry_result_um(instance)
        cell = self._engine.create_cell(key.cell_name)
        for poly in geometry.polygons:
            self._engine.add_polygon(
                cell,
                poly.vertices.tolist(),
                layer=self._profile.map_logical(poly.layer),
                datatype=poly.datatype,
            )
        self._cells[key] = cell
        return cell

    @property
    def size(self) -> int:
        return len(self._cells)

    @property
    def family_count(self) -> int:
        return len(self._family_counts)

    def family_stats(self) -> dict[str, int]:
        return {key.family_name: count for key, count in self._family_counts.items()}

