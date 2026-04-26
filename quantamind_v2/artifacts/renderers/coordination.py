from __future__ import annotations

from typing import Any

from quantamind_v2.artifacts.renderers.common import as_text
from quantamind_v2.contracts.artifact import ArtifactRecord


def render_coordination_report(artifact: ArtifactRecord) -> str:
    payload: dict[str, Any] = dict(artifact.payload or {})
    route = payload.get("route_result") or {}
    plan = payload.get("plan") or {}
    merged = payload.get("merged") or {}
    outputs: list[dict[str, Any]] = list(merged.get("outputs") or [])

    route_mode = as_text(route.get("mode")) or "unknown"
    route_reason = as_text(route.get("reason")) or "—"
    plan_steps = list(plan.get("steps") or [])
    merged_count = merged.get("count", len(outputs))
    merged_summary = as_text(merged.get("summary")) or "—"

    lines: list[str] = [
        f"# {artifact.title}",
        "",
        f"类型：{artifact.artifact_type.value}",
        f"运行：{artifact.run_id}",
        f"摘要：{artifact.summary or '—'}",
        "",
        "## Coordination",
        f"- mode: {route_mode}",
        f"- reason: {route_reason}",
        f"- steps: {len(plan_steps)}",
        f"- merged_count: {merged_count}",
        "",
        "## Merged Summary",
        merged_summary,
    ]
    if outputs:
        lines.extend(["", "## Child Outputs"])
        for idx, item in enumerate(outputs, start=1):
            owner = as_text(item.get("owner_agent")) or "unknown"
            summary = as_text(item.get("summary")) or as_text(item.get("status_message")) or "—"
            lines.append(f"{idx}. [{owner}] {summary}")

    return "\n".join(lines)
