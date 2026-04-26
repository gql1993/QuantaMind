"""
Export REST API endpoints for GDS/OASIS/Gerber file generation.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class ExportRequest(BaseModel):
    design_id: str
    format: str = "gds"
    output_path: str = ""
    run_drc: bool = True
    flatten: bool = False


@router.post("/gds")
async def export_gds(req: ExportRequest, request: Request) -> dict:
    svc = request.app.state.sidecar.design_service
    design = svc.get_design(req.design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    output = Path(req.output_path or f"exports/{design.name}.gds")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        from quantamind.server.geometry.export_gds import design_to_gds
        design_to_gds(design, output)
        return {"status": "ok", "design_id": req.design_id, "output_path": str(output)}
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_formats() -> list[dict]:
    return [
        {"format": "gds", "extension": ".gds", "description": "GDSII format"},
        {"format": "oasis", "extension": ".oas", "description": "OASIS format"},
        {"format": "gerber", "extension": ".gbr", "description": "Gerber RS-274X"},
        {"format": "svg", "extension": ".svg", "description": "SVG vector graphics"},
        {"format": "dxf", "extension": ".dxf", "description": "AutoCAD DXF"},
    ]
