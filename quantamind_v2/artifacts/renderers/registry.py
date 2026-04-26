from __future__ import annotations

from typing import Callable

from quantamind_v2.artifacts.renderers.coordination import render_coordination_report
from quantamind_v2.artifacts.renderers.generic import render_generic_report
from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType


Renderer = Callable[[ArtifactRecord], str]


_RENDERERS: dict[ArtifactType, Renderer] = {
    ArtifactType.COORDINATION_REPORT: render_coordination_report,
}


def register_renderer(artifact_type: ArtifactType, renderer: Renderer, *, replace: bool = False) -> None:
    if artifact_type in _RENDERERS and not replace:
        raise ValueError(f"renderer already registered for {artifact_type.value}")
    _RENDERERS[artifact_type] = renderer


def unregister_renderer(artifact_type: ArtifactType) -> bool:
    if artifact_type not in _RENDERERS:
        return False
    del _RENDERERS[artifact_type]
    return True


def list_registered_renderers() -> dict[str, str]:
    return {artifact_type.value: renderer.__name__ for artifact_type, renderer in _RENDERERS.items()}


def resolve_renderer(artifact_type: ArtifactType) -> Renderer:
    return _RENDERERS.get(artifact_type, render_generic_report)
