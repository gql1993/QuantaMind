from __future__ import annotations

import json

from quantamind_v2.contracts.artifact import ArtifactRecord


def render_generic_report(artifact: ArtifactRecord) -> str:
    payload_text = json.dumps(artifact.payload, ensure_ascii=False, default=str, indent=2)
    return (
        f"# {artifact.title}\n\n"
        f"类型：{artifact.artifact_type.value}\n"
        f"运行：{artifact.run_id}\n"
        f"摘要：{artifact.summary or '—'}\n\n"
        f"{payload_text}"
    )
