# 客户端-服务端 API 契约（REST + WebSocket）

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    stream: bool = True


class ChatChunk(BaseModel):
    """SSE/WebSocket 流式 chunk"""
    type: str = "content"  # content | done | error
    data: Optional[str] = None
    session_id: Optional[str] = None


class SessionCreate(BaseModel):
    project_id: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    project_id: Optional[str] = None
    created_at: str


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    title: Optional[str] = None
    task_type: Optional[str] = None
    created_at: Optional[str] = None
    session_id: Optional[str] = None
    needs_approval: bool = False


class HeartbeatStatus(BaseModel):
    level: str
    interval_minutes: int
    last_run: Optional[str] = None
    next_run: Optional[str] = None
