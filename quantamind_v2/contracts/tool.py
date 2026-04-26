from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class ToolClass(str, Enum):
    QUERY = "query"
    MUTATION = "mutation"
    LONG_RUNNING = "long_running"
    EXTERNAL_DELIVERY = "external_delivery"
    DEVICE_COMMAND = "device_command"


class ToolDescriptor(BaseModel):
    name: str
    description: str
    tool_class: ToolClass = ToolClass.QUERY
    metadata: Dict[str, Any] = Field(default_factory=dict)
