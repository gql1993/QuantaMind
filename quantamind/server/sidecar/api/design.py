"""
Design REST API endpoints.

CRUD operations for designs, components, topology, and routing.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class CreateDesignRequest(BaseModel):
    name: str
    topology_type: str = "custom"
    num_qubits: int = 0
    grid_rows: int = 0
    grid_cols: int = 0
    description: str = ""
    chip_size_x_mm: float = 10.0
    chip_size_y_mm: float = 10.0


class AddComponentRequest(BaseModel):
    definition_id: str
    name: str
    position_x: float = 0.0
    position_y: float = 0.0
    rotation: float = 0.0
    parameters: dict[str, Any] = Field(default_factory=dict)


class AddRouteRequest(BaseModel):
    source_instance_id: str
    source_port: str
    target_instance_id: str
    target_port: str
    width_um: float = 10.0
    gap_um: float = 6.0


class UpdateComponentRequest(BaseModel):
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    rotation: Optional[float] = None
    parameters: Optional[dict[str, Any]] = None


def _get_service(request: Request):
    return request.app.state.sidecar.design_service


@router.post("")
async def create_design(req: CreateDesignRequest, request: Request) -> dict:
    svc = _get_service(request)
    design = svc.create_design(
        name=req.name,
        topology_type=req.topology_type,
        num_qubits=req.num_qubits,
        grid_rows=req.grid_rows,
        grid_cols=req.grid_cols,
        description=req.description,
        chip_size_x_mm=req.chip_size_x_mm,
        chip_size_y_mm=req.chip_size_y_mm,
    )
    return {"design_id": design.design_id, "name": design.name}


@router.get("")
async def list_designs(request: Request) -> list[dict]:
    svc = _get_service(request)
    return [
        {
            "design_id": d.design_id,
            "name": d.name,
            "state": d.state.value,
            "num_components": d.num_components,
            "num_routes": d.num_routes,
        }
        for d in svc.list_designs()
    ]


@router.get("/{design_id}")
async def get_design(design_id: str, request: Request) -> dict:
    svc = _get_service(request)
    design = svc.get_design(design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    return design.model_dump(mode="json")


@router.post("/import")
async def import_design(request: Request) -> dict:
    """从 JSON 导入设计（用于打开文件）。"""
    from quantamind.server.qeda_models.design import Design
    from quantamind.server.services.external_design_importer import (
        import_external_design_dict,
        is_external_design_payload,
    )

    body = await request.json()
    svc = _get_service(request)
    try:
        try:
            design = Design.model_validate(body)
            import_report = None
        except Exception:
            if not is_external_design_payload(body):
                raise
            design, import_report = import_external_design_dict(
                body,
                design_name=body.get("name", "Imported External Design")
                if isinstance(body, dict)
                else "Imported External Design",
            )
        svc._designs[design.design_id] = design
        svc._active_design_id = design.design_id
        payload = {
            "design_id": design.design_id,
            "name": design.name,
            "design": design.model_dump(mode="json"),
        }
        if import_report is not None:
            payload["import_report"] = import_report
            payload["import_format"] = "external_qiskit_json"
        return payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{design_id}")
async def close_design(design_id: str, request: Request) -> dict:
    svc = _get_service(request)
    if not svc.close_design(design_id):
        raise HTTPException(status_code=404, detail="Design not found")
    return {"status": "closed"}


@router.post("/{design_id}/components")
async def add_component(design_id: str, req: AddComponentRequest, request: Request) -> dict:
    svc = _get_service(request)
    try:
        comp = svc.add_component(
            design_id=design_id,
            definition_id=req.definition_id,
            name=req.name,
            position_x=req.position_x,
            position_y=req.position_y,
            rotation=req.rotation,
            parameters=req.parameters,
        )
        return {"instance_id": comp.instance_id, "name": comp.name}
    except KeyError:
        raise HTTPException(status_code=404, detail="Design not found")


@router.patch("/{design_id}/components/{instance_id}")
async def update_component(
    design_id: str, instance_id: str, req: UpdateComponentRequest, request: Request
) -> dict:
    svc = _get_service(request)
    design = svc.get_design(design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    comp = design.get_component(instance_id)
    if comp is None:
        raise HTTPException(status_code=404, detail="Component not found")

    if req.position_x is not None:
        comp.position_x = req.position_x
    if req.position_y is not None:
        comp.position_y = req.position_y
    if req.rotation is not None:
        comp.rotation = req.rotation
    if req.parameters is not None:
        comp.parameters.update(req.parameters)

    return {"status": "updated", "instance_id": instance_id}


@router.delete("/{design_id}/components/{instance_id}")
async def remove_component(design_id: str, instance_id: str, request: Request) -> dict:
    svc = _get_service(request)
    try:
        if not svc.remove_component(instance_id, design_id):
            raise HTTPException(status_code=404, detail="Component not found")
        return {"status": "removed"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Design not found")


@router.post("/{design_id}/routes")
async def add_route(design_id: str, req: AddRouteRequest, request: Request) -> dict:
    svc = _get_service(request)
    try:
        seg = svc.add_route(
            source_id=req.source_instance_id,
            source_port=req.source_port,
            target_id=req.target_instance_id,
            target_port=req.target_port,
            design_id=design_id,
            width_um=req.width_um,
            gap_um=req.gap_um,
        )
        return {"segment_id": seg.segment_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="Design not found")


@router.get("/{design_id}/topology")
async def get_topology(design_id: str, request: Request) -> dict:
    svc = _get_service(request)
    design = svc.get_design(design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    return design.topology.model_dump(mode="json")


@router.post("/{design_id}/save")
async def save_design(design_id: str, request: Request, path: str = "") -> dict:
    svc = _get_service(request)
    try:
        saved_path = svc.save_design(design_id, path or None)
        return {"status": "saved", "path": str(saved_path)}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
