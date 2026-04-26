from __future__ import annotations

from pydantic import BaseModel, Field

from quantamind_v2.contracts.approval import ApprovalType


class ShortcutRunRequest(BaseModel):
    force: bool = False
    origin: str = "manual"


class CoordinationRunRequest(BaseModel):
    message: str
    origin: str = "manual"
    profile_id: str = "default"
    conflict_strategy: str | None = None
    priority: str = "normal"
    budget_seconds: float | None = Field(default=None, gt=0)


class CoordinationConflictPolicyUpdateRequest(BaseModel):
    profile_id: str = "default"
    strategy: str
    source: str = "manual"


class CoordinationCutoverControlUpdateRequest(BaseModel):
    profile_allowlist: list[str] | None = None
    rollout_percentage: int | None = Field(default=None, ge=0, le=100)
    source: str = "manual"


class ShortcutTaskRequest(BaseModel):
    force: bool = False
    origin: str = "manual"
    budget_seconds: float | None = None
    max_retries: int = 0


class ApprovalCreateRequest(BaseModel):
    run_id: str
    approval_type: ApprovalType
    summary: str
    details: dict = Field(default_factory=dict)


class ApprovalResolveRequest(BaseModel):
    reviewer: str = "reviewer"
    comment: str = ""


class PipelineExecuteRequest(BaseModel):
    template: str = "standard_daily_ops"
    origin: str = "manual"
    force: bool = False
    background: bool = True


class ModelMessageInput(BaseModel):
    role: str
    content: str


class ModelInferRequest(BaseModel):
    provider: str | None = None
    model: str | None = None
    prompt: str = ""
    messages: list[ModelMessageInput] = Field(default_factory=list)
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout_seconds: float | None = None
    metadata: dict = Field(default_factory=dict)


class MCPInvokeRequest(BaseModel):
    tool: str
    args: dict = Field(default_factory=dict)
    timeout_seconds: float | None = None


class ProjectMemoryNoteRequest(BaseModel):
    content: str
    source: str = "manual"
    metadata: dict = Field(default_factory=dict)


class PlanningPreviewRequest(BaseModel):
    message: str
    priority: str = "normal"
    budget_seconds: float | None = Field(default=None, gt=0)


class KnowledgeIndexRequest(BaseModel):
    title: str
    content: str
    source: str = "manual"
    metadata: dict = Field(default_factory=dict)


class WorkspacePanelInput(BaseModel):
    panel_id: str
    title: str
    order: int
    visible: bool = True
    source: str = "shared_state"
    metadata: dict = Field(default_factory=dict)


class WorkspaceLayoutCreateRequest(BaseModel):
    layout_id: str
    name: str
    target: str = "web"
    panels: list[WorkspacePanelInput] = Field(default_factory=list)


class ClientShortcutsPreferenceRequest(BaseModel):
    pinned_shortcuts: list[str] = Field(default_factory=list)


class ClientLayoutSyncRequest(BaseModel):
    source_target: str = "web"
    target: str = "desktop"


class WorkspaceRecoveryCreateRequest(BaseModel):
    run_id: str | None = None
    task_id: str | None = None
    artifact_id: str | None = None
    note: str = ""
    metadata: dict = Field(default_factory=dict)


class SessionLeaseCreateRequest(BaseModel):
    profile_id: str = "default"
    client_type: str = "web"
    client_id: str
    access_mode: str = "reader"
    allow_handover: bool = False
    lease_seconds: int = 60
    metadata: dict = Field(default_factory=dict)


class SessionHeartbeatRequest(BaseModel):
    lease_seconds: int = 60
