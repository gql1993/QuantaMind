from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.quantamind_api.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


def _chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post("")
async def chat(request: Request, payload: ChatRequest) -> dict:
    try:
        result = await _chat_service(request).send(payload.message, session_id=payload.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "success": True,
        "data": {
            "content": result.content,
            "run_id": result.run_id,
            "pipeline_id": result.pipeline_id,
        },
        "error": None,
    }


@router.post("/stream")
async def chat_stream(request: Request, payload: ChatRequest) -> StreamingResponse:
    async def event_stream():
        async for event in _chat_service(request).stream(payload.message, session_id=payload.session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
