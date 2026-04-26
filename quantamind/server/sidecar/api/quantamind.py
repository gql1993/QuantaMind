"""
QuantaMind 量智大脑代理 API - 聊天与工具调用
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str = ""
    agent: str = ""


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """转发聊天请求到 QuantaMind Gateway。"""
    sidecar = request.app.state.sidecar
    client = getattr(sidecar, "quantamind_client", None)
    if not client or not client.connected:
        return ChatResponse(
            response="QuantaMind 未连接。请确保 QuantaMind Gateway 在 localhost:18789 运行。",
            session_id="",
        )

    try:
        if req.stream:
            chunks = []
            async for chunk in client.chat_stream(req.message):
                chunks.append(chunk)
            return ChatResponse(
                response="".join(chunks),
                session_id=client.session_id,
            )
        else:
            response = await client.chat(req.message)
            return ChatResponse(
                response=response,
                session_id=client.session_id,
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/status")
async def quantamind_status(request: Request) -> dict:
    """QuantaMind 连接状态。"""
    sidecar = request.app.state.sidecar
    client = getattr(sidecar, "quantamind_client", None)
    return {
        "connected": client.connected if client else False,
        "session_id": client.session_id if client else "",
    }
