from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RunEvent(BaseModel):
    event_id: str
    run_id: str
    event_type: str
    timestamp: str = Field(default_factory=utc_now_iso)
    payload: Dict[str, Any] = Field(default_factory=dict)
