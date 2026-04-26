from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn


app = FastAPI(
    title="CHIPMES Quickstart",
    description="Fast compatibility service for QuantaMind",
    version="0.1.0",
)


_SYSTEM_INFO = {
    "system": "CHIPMES 半导体制造执行系统",
    "mode": "compatibility",
    "version": "9.0-fast",
    "framework": "FastAPI compatibility layer",
    "port": 8082,
    "modules": {
        "cm": "芯片管理（Chip Management）",
        "fm": "制造管理（Fabrication Management）",
        "pm": "计划管理（Plan Management）",
    },
    "features": [
        "主订单/子订单管理",
        "工艺路线管理",
        "批次跟踪",
        "设备管理",
        "良率统计",
        "SPC 过程监控",
        "Swagger API 文档",
    ],
}

_ORDERS = [
    {"order_id": "WO-2026-001", "product": "20bit-Transmon", "qty": 24, "status": "生产中", "priority": "高"},
    {"order_id": "WO-2026-002", "product": "105bit-Transmon", "qty": 12, "status": "待排产", "priority": "中"},
    {"order_id": "WO-2026-003", "product": "JJ-Test", "qty": 48, "status": "已完成", "priority": "低"},
]

_CRAFTS = [
    {"route_id": "CR-001", "name": "超导量子芯片全流程", "steps": ["衬底清洗", "Nb/Ta 溅射", "光刻", "RIE 刻蚀", "JJ 制备(Dolan)", "空气桥", "布线", "封装"]},
    {"route_id": "CR-002", "name": "JJ 单步测试", "steps": ["清洗", "EBL 曝光", "双角蒸镀", "Lift-off", "电学测试"]},
]

_EQUIPMENT = [
    {"eq_id": "SPUTTER-01", "name": "磁控溅射台", "type": "薄膜沉积", "status": "运行"},
    {"eq_id": "LITHO-01", "name": "激光直写机", "type": "光刻", "status": "运行"},
    {"eq_id": "EBL-01", "name": "电子束曝光机", "type": "EBL", "status": "运行"},
    {"eq_id": "ETCH-01", "name": "RIE 刻蚀机", "type": "刻蚀", "status": "维护中"},
]

_YIELD = [
    {"lot": "LOT-2026-0301", "product": "20bit-Transmon", "yield_pct": 91.7, "defects": 2, "total": 24},
    {"lot": "LOT-2026-0285", "product": "20bit-Transmon", "yield_pct": 95.8, "defects": 1, "total": 24},
    {"lot": "LOT-2026-0302", "product": "105bit-Transmon", "yield_pct": 87.5, "defects": 3, "total": 24},
]


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "CHIPMES Quickstart",
        "message": "QuantaMind compatibility service is running",
    }


@app.get("/actuator/info")
def actuator_info():
    return _SYSTEM_INFO


@app.get("/swagger-ui.html")
def swagger_ui():
    return RedirectResponse(url="/docs")


@app.get("/v3/api-docs")
def openapi_docs():
    return {
        "openapi": "3.0.0",
        "info": {"title": "CHIPMES Quickstart", "version": "0.1.0"},
        "paths": {
            "/actuator/info": {"get": {"summary": "system info"}},
            "/api/plan/ordermain": {"get": {"summary": "orders"}},
            "/api/base/craft": {"get": {"summary": "craft routes"}},
            "/api/base/equipment": {"get": {"summary": "equipment"}},
            "/api/report/yield": {"get": {"summary": "yield report"}},
        },
    }


@app.get("/api/plan/ordermain")
def ordermain(status: str | None = None):
    if status:
        return [o for o in _ORDERS if o["status"] == status]
    return _ORDERS


@app.get("/api/base/craft")
def crafts():
    return _CRAFTS


@app.get("/api/base/equipment")
def equipment():
    return _EQUIPMENT


@app.get("/api/report/yield")
def yield_report(product: str | None = None):
    if product:
        return [y for y in _YIELD if y["product"] == product]
    return _YIELD


@app.get("/health")
def health():
    return {"status": "ok", "service": "CHIPMES Quickstart"}


def run():
    uvicorn.run("quantamind.server.chipmes_quickstart:app", host="127.0.0.1", port=8082, reload=False)


if __name__ == "__main__":
    run()
