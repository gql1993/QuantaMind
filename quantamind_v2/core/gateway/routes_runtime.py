from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from quantamind_v2.core.gateway.deps import GatewayDeps
from quantamind_v2.core.gateway.schemas import MCPInvokeRequest, ModelInferRequest
from quantamind_v2.runtimes.models import ModelMessage, ModelRequest


def build_runtime_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v2/tasks")
    async def list_tasks(state: str | None = Query(default=None)) -> dict:
        items = deps.tasks.list()
        if state:
            normalized = state.strip().lower()
            items = [task for task in items if task.state.value == normalized]
        items = sorted(items, key=lambda item: item.updated_at, reverse=True)
        return {"items": [item.model_dump() for item in items]}

    @router.get("/api/v2/tasks/{task_id}")
    async def get_task(task_id: str) -> dict:
        try:
            task = deps.tasks.get(task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return task.model_dump()

    @router.post("/api/v2/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict:
        try:
            task = deps.tasks.cancel(task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"task": task.model_dump()}

    @router.post("/api/v2/tasks/{task_id}/retry")
    async def retry_task(task_id: str) -> dict:
        try:
            task = deps.tasks.retry(task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"task": task.model_dump()}

    @router.get("/api/v2/models/providers")
    async def list_model_providers() -> dict:
        return {"items": deps.model_runtime.list_providers()}

    @router.post("/api/v2/models/infer")
    async def infer_with_model(body: ModelInferRequest) -> dict:
        request = ModelRequest(
            provider=body.provider,
            model=body.model,
            prompt=body.prompt,
            messages=[ModelMessage(role=item.role, content=item.content) for item in body.messages],
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            metadata=dict(body.metadata or {}),
        )
        try:
            result = await deps.model_runtime.generate(request, timeout_seconds=body.timeout_seconds)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {
            "used_provider": result.used_provider,
            "requested_provider": result.requested_provider,
            "fallback_used": result.fallback_used,
            "response": {
                "provider": result.response.provider,
                "model": result.response.model,
                "text": result.response.text,
                "usage": result.response.usage,
                "metadata": result.response.metadata,
            },
        }

    @router.get("/api/v2/mcp/tools")
    async def list_mcp_tools() -> dict:
        return {"items": deps.mcp_host.list_tools()}

    @router.post("/api/v2/mcp/invoke")
    async def invoke_mcp_tool(body: MCPInvokeRequest) -> dict:
        try:
            result = await deps.mcp_host.invoke(
                body.tool,
                args=dict(body.args or {}),
                timeout_seconds=body.timeout_seconds,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {
            "tool": result.tool,
            "output": result.output,
            "metadata": result.metadata,
        }

    return router
