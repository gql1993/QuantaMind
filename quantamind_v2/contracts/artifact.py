from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ArtifactType(str, Enum):
    INTEL_REPORT = "intel_report"
    PIPELINE_REPORT = "pipeline_report"
    SYSTEM_DIAGNOSIS = "system_diagnosis"
    DB_HEALTH_REPORT = "db_health_report"
    LIBRARY_INGEST_REPORT = "library_ingest_report"
    COORDINATION_REPORT = "coordination_report"
    GENERIC = "generic_artifact"


class ArtifactRecord(BaseModel):
    artifact_id: str
    run_id: str
    artifact_type: ArtifactType
    title: str
    summary: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
