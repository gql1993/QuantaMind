from __future__ import annotations

from typing import Any

from quantamind_v2.client.shared.models import (
    SharedArtifactView,
    SharedClientState,
    SharedRunView,
    SharedTaskView,
)


def normalize_run(payload: dict[str, Any], *, event_count: int = 0) -> SharedRunView:
    artifacts = payload.get("artifacts") or []
    return SharedRunView(
        run_id=str(payload.get("run_id", "")),
        run_type=str(payload.get("run_type", "unknown")),
        state=str(payload.get("state", "unknown")),
        stage=str(payload.get("stage", "")),
        owner_agent=payload.get("owner_agent"),
        status_message=str(payload.get("status_message", "")),
        artifact_count=len(artifacts),
        event_count=int(event_count),
        updated_at=str(payload.get("updated_at", "")),
        metadata=dict(payload.get("metadata") or {}),
    )


def normalize_task(payload: dict[str, Any]) -> SharedTaskView:
    return SharedTaskView(
        task_id=str(payload.get("task_id", "")),
        task_name=str(payload.get("task_name", "")),
        run_id=payload.get("run_id"),
        state=str(payload.get("state", "unknown")),
        attempt=int(payload.get("attempt", 1)),
        max_retries=int(payload.get("max_retries", 0)),
        budget_seconds=payload.get("budget_seconds"),
        updated_at=str(payload.get("updated_at", "")),
        error=str(payload.get("error", "")),
        result=payload.get("result"),
    )


def normalize_artifact(payload: dict[str, Any]) -> SharedArtifactView:
    return SharedArtifactView(
        artifact_id=str(payload.get("artifact_id", "")),
        run_id=str(payload.get("run_id", "")),
        artifact_type=str(payload.get("artifact_type", "generic_artifact")),
        title=str(payload.get("title", "")),
        summary=str(payload.get("summary", "")),
        created_at=str(payload.get("created_at", "")),
    )


def build_shared_client_state(
    *,
    runs: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    run_event_counts: dict[str, int] | None = None,
) -> SharedClientState:
    event_counts = run_event_counts or {}
    run_views = [
        normalize_run(item, event_count=event_counts.get(str(item.get("run_id", "")), 0))
        for item in runs
    ]
    task_views = [normalize_task(item) for item in tasks]
    artifact_views = [normalize_artifact(item) for item in artifacts]
    return SharedClientState(runs=run_views, tasks=task_views, artifacts=artifact_views)
