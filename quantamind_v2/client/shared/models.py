from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SharedRunView:
    run_id: str
    run_type: str
    state: str
    stage: str
    owner_agent: str | None
    status_message: str
    artifact_count: int = 0
    event_count: int = 0
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SharedTaskView:
    task_id: str
    task_name: str
    run_id: str | None
    state: str
    attempt: int
    max_retries: int
    budget_seconds: float | None
    updated_at: str = ""
    error: str = ""
    result: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SharedArtifactView:
    artifact_id: str
    run_id: str
    artifact_type: str
    title: str
    summary: str
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SharedClientState:
    runs: list[SharedRunView] = field(default_factory=list)
    tasks: list[SharedTaskView] = field(default_factory=list)
    artifacts: list[SharedArtifactView] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runs": [item.to_dict() for item in self.runs],
            "tasks": [item.to_dict() for item in self.tasks],
            "artifacts": [item.to_dict() for item in self.artifacts],
            "summary": {
                "run_total": len(self.runs),
                "run_running": sum(1 for item in self.runs if item.state == "running"),
                "run_failed": sum(1 for item in self.runs if item.state == "failed"),
                "task_total": len(self.tasks),
                "task_running": sum(1 for item in self.tasks if item.state == "running"),
                "artifact_total": len(self.artifacts),
            },
        }
