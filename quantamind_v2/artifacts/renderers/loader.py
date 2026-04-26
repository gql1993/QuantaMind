from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from quantamind_v2.artifacts.renderers.registry import Renderer, register_renderer
from quantamind_v2.contracts.artifact import ArtifactType


DEFAULT_REGISTRY_CONFIG = Path(__file__).with_name("registry_config.json")


def _resolve_artifact_type(raw: str) -> ArtifactType | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        return ArtifactType(value)
    except ValueError:
        pass
    try:
        return ArtifactType[value.upper()]
    except KeyError:
        return None


def _resolve_renderer(spec: str) -> Renderer:
    module_name, sep, symbol = spec.partition(":")
    if not sep:
        raise ValueError(f"renderer spec must be 'module_path:symbol', got: {spec}")
    module = importlib.import_module(module_name)
    target = getattr(module, symbol, None)
    if target is None:
        raise ValueError(f"renderer symbol not found: {spec}")
    if not callable(target):
        raise ValueError(f"renderer target is not callable: {spec}")
    return target


def load_and_register_renderers(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path is not None else DEFAULT_REGISTRY_CONFIG
    report: dict[str, Any] = {
        "path": str(path),
        "loaded": False,
        "registered": [],
        "warnings": [],
    }
    if not path.exists():
        report["warnings"].append("renderer registry config file not found; defaults only")
        return report

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        report["warnings"].append(f"failed to parse renderer registry config: {exc}")
        return report

    mappings = payload.get("renderers") if isinstance(payload, dict) else None
    if not isinstance(mappings, dict):
        report["warnings"].append("invalid renderer registry config: missing object field `renderers`")
        return report

    report["loaded"] = True
    for raw_type, raw_renderer in mappings.items():
        artifact_type = _resolve_artifact_type(str(raw_type))
        if artifact_type is None:
            report["warnings"].append(f"unknown artifact type: {raw_type}")
            continue
        try:
            renderer = _resolve_renderer(str(raw_renderer))
            register_renderer(artifact_type, renderer, replace=True)
            report["registered"].append({"artifact_type": artifact_type.value, "renderer": str(raw_renderer)})
        except Exception as exc:  # noqa: BLE001
            report["warnings"].append(f"failed to register renderer for {raw_type}: {exc}")
    return report
