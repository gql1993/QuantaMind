from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RunState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunType(str, Enum):
    CHAT = "chat_run"
    DIGEST = "digest_run"
    PIPELINE = "pipeline_run"
    IMPORT = "import_run"
    SIMULATION = "simulation_run"
    CALIBRATION = "calibration_run"
    DATA_SYNC = "data_sync_run"
    SYSTEM = "system_run"
    REPAIR = "repair_run"


class RunRecord(BaseModel):
    run_id: str
    run_type: RunType
    origin: str = "manual"
    parent_run_id: Optional[str] = None
    state: RunState = RunState.QUEUED
    stage: str = "queued"
    status_message: str = ""
    owner_agent: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None
