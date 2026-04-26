from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from quantamind.server import state_store
from quantamind_v2.artifacts import InMemoryArtifactStore
from quantamind_v2.core.runs.coordinator import RunCoordinator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _normalize_state(value: Any) -> str:
    text = _as_text(value, "queued").strip().lower()
    mapping = {
        "pending": "queued",
        "created": "queued",
        "queued": "queued",
        "running": "running",
        "paused": "running",
        "completed": "completed",
        "done": "completed",
        "success": "completed",
        "failed": "failed",
        "error": "failed",
        "aborted": "cancelled",
        "cancelled": "cancelled",
    }
    return mapping.get(text, "queued")


def _infer_run_type(task_type: str) -> str:
    text = task_type.lower()
    if "sim" in text or "仿真" in text:
        return "simulation_run"
    if "measure" in text or "calib" in text or "测" in text or "校准" in text:
        return "calibration_run"
    if "pipeline" in text or "mes" in text or "制造" in text:
        return "pipeline_run"
    if "data" in text or "sync" in text:
        return "data_sync_run"
    return "system_run"


def _task_to_run(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    status = _normalize_state(payload.get("status"))
    task_type = _as_text(payload.get("task_type"), "task")
    created_at = _as_text(payload.get("created_at"), _now_iso())
    return {
        "run_id": f"v1-task-{task_id}",
        "run_type": _infer_run_type(task_type),
        "origin": "v1_task",
        "parent_run_id": None,
        "state": status,
        "stage": "approval_required" if payload.get("needs_approval") else status,
        "status_message": _as_text(payload.get("title"), "V1 task"),
        "owner_agent": payload.get("agent_id") or payload.get("agent") or None,
        "artifacts": [],
        "events": [],
        "metadata": {
            "source": "v1_state_store",
            "source_type": "task",
            "source_id": task_id,
            "task_type": task_type,
            "needs_approval": bool(payload.get("needs_approval")),
            "result": payload.get("result"),
            "error": payload.get("error"),
        },
        "created_at": created_at,
        "updated_at": _as_text(payload.get("updated_at"), created_at),
        "completed_at": created_at if status == "completed" else None,
    }


def _pipeline_to_run(pipeline_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = _normalize_state(payload.get("status"))
    created_at = _as_text(payload.get("created_at"), _now_iso())
    steps = payload.get("steps") or []
    current_stage = payload.get("current_stage", 0)
    return {
        "run_id": f"v1-pipeline-{pipeline_id}",
        "run_type": "pipeline_run",
        "origin": "v1_pipeline",
        "parent_run_id": None,
        "state": state,
        "stage": _as_text(payload.get("current_step"), f"stage_{current_stage}"),
        "status_message": _as_text(payload.get("name"), "V1 pipeline"),
        "owner_agent": payload.get("agent_id") or payload.get("agent_label") or None,
        "artifacts": [f"artifact-v1-pipeline-{pipeline_id}"],
        "events": [],
        "metadata": {
            "source": "v1_state_store",
            "source_type": "pipeline",
            "source_id": pipeline_id,
            "template": payload.get("template"),
            "steps_count": len(steps),
            "current_stage": current_stage,
            "paused": bool(payload.get("paused")),
            "aborted": bool(payload.get("aborted")),
        },
        "created_at": created_at,
        "updated_at": _as_text(payload.get("updated_at"), created_at),
        "completed_at": created_at if state == "completed" else None,
    }


class RuntimeStateService:
    def __init__(self, coordinator: RunCoordinator, artifact_store: InMemoryArtifactStore) -> None:
        self.coordinator = coordinator
        self.artifact_store = artifact_store

    def list_runs(self) -> list[dict[str, Any]]:
        runs = [self._v2_run_to_dict(run.model_dump()) for run in self.coordinator.list_runs()]
        runs.extend(self._load_v1_task_runs())
        runs.extend(self._load_v1_pipeline_runs())
        return sorted(runs, key=lambda item: item.get("updated_at") or "", reverse=True)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        for run in self.list_runs():
            if run["run_id"] == run_id:
                return run
        return None

    def list_events(self, run_id: str) -> list[dict[str, Any]]:
        if run_id.startswith("v1-"):
            run = self.get_run(run_id)
            if not run:
                return []
            return [
                {
                    "event_id": f"event-{run_id}-compat",
                    "run_id": run_id,
                    "event_type": "compat_state_loaded",
                    "payload": {
                        "source": run.get("metadata", {}).get("source"),
                        "source_type": run.get("metadata", {}).get("source_type"),
                    },
                    "created_at": run.get("updated_at") or _now_iso(),
                }
            ]
        return [event.model_dump() for event in self.coordinator.list_events(run_id)]

    def list_artifacts(self, run_id: str | None = None) -> list[dict[str, Any]]:
        artifacts = self.artifact_store.list_for_run(run_id) if run_id else self.artifact_store.list()
        items = [artifact.model_dump() for artifact in artifacts]
        items.extend(self._load_v1_pipeline_artifacts(run_id))
        return sorted(items, key=lambda item: item.get("created_at") or "", reverse=True)

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        artifact = self.artifact_store.get(artifact_id)
        if artifact is not None:
            return artifact.model_dump()
        for item in self._load_v1_pipeline_artifacts(None):
            if item["artifact_id"] == artifact_id:
                return item
        return None

    def _v2_run_to_dict(self, run: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(run.get("metadata") or {})
        metadata.setdefault("source", "v2_run_coordinator")
        run["metadata"] = metadata
        return run

    def _load_v1_task_runs(self) -> list[dict[str, Any]]:
        return [_task_to_run(task_id, payload) for task_id, payload in state_store.load_tasks().items()]

    def _load_v1_pipeline_runs(self) -> list[dict[str, Any]]:
        return [
            _pipeline_to_run(pipeline_id, payload)
            for pipeline_id, payload in state_store.load_pipelines().items()
        ]

    def _load_v1_pipeline_artifacts(self, run_id: str | None) -> list[dict[str, Any]]:
        artifacts = []
        for pipeline_id, payload in state_store.load_pipelines().items():
            compat_run_id = f"v1-pipeline-{pipeline_id}"
            if run_id and run_id != compat_run_id:
                continue
            created_at = _as_text(payload.get("created_at"), _now_iso())
            artifacts.append(
                {
                    "artifact_id": f"artifact-v1-pipeline-{pipeline_id}",
                    "run_id": compat_run_id,
                    "artifact_type": "pipeline_report",
                    "title": _as_text(payload.get("name"), "V1 pipeline report"),
                    "summary": f"兼容 V1 流水线产物，步骤数：{len(payload.get('steps') or [])}",
                    "payload": {
                        "source": "v1_state_store",
                        "source_type": "pipeline",
                        "source_id": pipeline_id,
                        "status": payload.get("status"),
                        "current_stage": payload.get("current_stage"),
                    },
                    "created_at": created_at,
                }
            )
        return artifacts
