from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ApprovalType(str, Enum):
    SHELL = "shell"
    EXTERNAL_DELIVERY = "external_delivery"
    FILE_MUTATION = "file_mutation"
    DATABASE_MUTATION = "database_mutation"
    DEVICE_COMMAND = "device_command"
    MES_OPERATION = "mes_operation"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    approval_id: str
    run_id: str
    approval_type: ApprovalType
    status: ApprovalStatus = ApprovalStatus.PENDING
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    reviewer: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    resolved_at: Optional[str] = None
