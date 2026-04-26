"""
QuantaMind message protocol definitions (QEDA bridge).

Defines JSON message shapes for chat, tool calls, streaming, and heartbeats.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageType(str, Enum):
    CHAT = "chat"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CONTENT = "content"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    TOOL_REGISTER = "tool_register"
    STATUS_UPDATE = "status_update"


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    DESIGNER = "designer_agent"
    SIMULATION = "simulation_agent"
    PHYSICIST = "physicist_agent"
    PROCESS_ENGINEER = "process_agent"
    THEORIST = "theorist_agent"


class ChatMessage(BaseModel):
    """Message sent from a QEDA-style client to QuantaMind Gateway."""
    message: str
    session_id: str = ""
    project_id: str = ""
    agent: Optional[str] = None
    stream: bool = True
    context: dict[str, Any] = Field(default_factory=dict)


class ToolCallMessage(BaseModel):
    """Tool call request from QuantaMind agent to the client."""
    type: str = MessageType.TOOL_CALL
    agent: str = ""
    tool: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    timestamp: datetime = Field(default_factory=_utcnow)


class ToolResultMessage(BaseModel):
    """Tool execution result from the client back to QuantaMind."""
    type: str = MessageType.TOOL_RESULT
    request_id: str = ""
    tool: str = ""
    success: bool = True
    result: Any = None
    error: str = ""
    timestamp: datetime = Field(default_factory=_utcnow)


class StreamChunk(BaseModel):
    """Streaming response chunk from QuantaMind."""
    type: str = MessageType.CONTENT
    data: str = ""
    session_id: str = ""
    agent: str = ""
    pipeline_id: str = ""


class ToolRegistration(BaseModel):
    """Tool definition registered with QuantaMind Gateway."""
    name: str
    description: str
    category: str = "qeda"
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class HeartbeatPayload(BaseModel):
    """Heartbeat data sent to QuantaMind periodically."""
    type: str = MessageType.HEARTBEAT
    active_design: Optional[str] = None
    design_state: str = ""
    num_components: int = 0
    num_qubits: int = 0
    latest_sim_summary: str = ""
    drc_status: str = "clean"
    timestamp: datetime = Field(default_factory=_utcnow)


class DesignStatusReport(BaseModel):
    """Detailed design status for QuantaMind context."""
    design_name: str = ""
    topology_type: str = ""
    num_qubits: int = 0
    num_couplers: int = 0
    num_resonators: int = 0
    frequency_range_ghz: tuple[float, float] = (0.0, 0.0)
    drc_errors: int = 0
    drc_warnings: int = 0
    simulation_jobs_active: int = 0
    last_simulation_result: str = ""
