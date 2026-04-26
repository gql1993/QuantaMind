from __future__ import annotations

from quantamind_v2.artifacts.renderers import resolve_renderer
from quantamind_v2.contracts.artifact import ArtifactRecord
from quantamind_v2.artifacts.schema import ArtifactRenderType, ArtifactView


def render_artifact_text(artifact: ArtifactRecord) -> ArtifactView:
    renderer = resolve_renderer(artifact.artifact_type)
    content = renderer(artifact)
    return ArtifactView(
        artifact_id=artifact.artifact_id,
        run_id=artifact.run_id,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        summary=artifact.summary,
        render_type=ArtifactRenderType.TEXT,
        content=content,
        metadata={"created_at": artifact.created_at},
    )
