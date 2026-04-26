from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType


class ArtifactRenderType(str, Enum):
    TEXT = "text"
    JSON = "json"


class ArtifactView(BaseModel):
    artifact_id: str
    run_id: str
    artifact_type: ArtifactType
    title: str
    summary: str = ""
    render_type: ArtifactRenderType = ArtifactRenderType.TEXT
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactList(BaseModel):
    items: List[ArtifactRecord] = Field(default_factory=list)
