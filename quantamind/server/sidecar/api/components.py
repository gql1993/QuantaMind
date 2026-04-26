"""
元件库 API - 提供 ComponentDefinition 列表供 UI 使用

UI 通过此端点获取元件库，避免直接实例化 ComponentService，保持分层。
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
async def list_components(request: Request) -> list[dict]:
    """获取元件库中所有元件定义。"""
    sidecar = request.app.state.sidecar
    comps = sidecar.component_service.list_all()
    return [c.model_dump(mode="json") for c in comps]


@router.get("/{component_id}")
async def get_component(component_id: str, request: Request) -> dict | None:
    """根据 ID 获取单个元件定义。"""
    sidecar = request.app.state.sidecar
    comp = sidecar.component_service.get(component_id)
    if comp is None:
        return None
    return comp.model_dump(mode="json")
