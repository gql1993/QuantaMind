from __future__ import annotations

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class ContextLayerType(str, Enum):
    SYSTEM = "system"
    AGENT_IDENTITY = "agent_identity"
    PROJECT_MEMORY = "project_memory"
    RECENT_CONVERSATION = "recent_conversation"
    ARTIFACT = "artifact"
    DATA_SNAPSHOT = "data_snapshot"
    TOOL_RESULT = "tool_result"
    POLICY = "policy"


class ContextLayer(BaseModel):
    layer_type: ContextLayerType
    content: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class ContextBundle(BaseModel):
    layers: List[ContextLayer] = Field(default_factory=list)
