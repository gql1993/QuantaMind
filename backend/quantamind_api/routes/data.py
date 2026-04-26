from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/data", tags=["data"])


DATASETS = [
    {
        "dataset_id": "design-parameters",
        "name": "芯片设计参数库",
        "domain": "design",
        "owner": "芯片设计组",
        "record_count": 12840,
        "quality_score": 96,
        "last_sync_at": "2026-04-26T08:30:00Z",
        "status": "healthy",
    },
    {
        "dataset_id": "measurement-results",
        "name": "测控实验结果",
        "domain": "measurement",
        "owner": "测控平台组",
        "record_count": 6421,
        "quality_score": 91,
        "last_sync_at": "2026-04-26T07:45:00Z",
        "status": "healthy",
    },
    {
        "dataset_id": "manufacturing-events",
        "name": "制造过程事件",
        "domain": "manufacturing",
        "owner": "制造工艺组",
        "record_count": 2319,
        "quality_score": 84,
        "last_sync_at": "2026-04-25T21:10:00Z",
        "status": "warning",
    },
]


@router.get("/catalog")
def list_datasets() -> dict:
    return {
        "success": True,
        "data": {
            "items": DATASETS,
            "total": len(DATASETS),
        },
        "error": None,
    }


@router.get("/quality")
def data_quality_summary() -> dict:
    average_score = round(sum(item["quality_score"] for item in DATASETS) / len(DATASETS), 1)
    warning_count = len([item for item in DATASETS if item["status"] != "healthy"])
    return {
        "success": True,
        "data": {
            "average_score": average_score,
            "healthy_count": len(DATASETS) - warning_count,
            "warning_count": warning_count,
            "rules": [
                {"rule_id": "freshness", "label": "同步新鲜度", "status": "ok"},
                {"rule_id": "completeness", "label": "字段完整率", "status": "ok"},
                {"rule_id": "manufacturing_gap", "label": "制造事件缺口", "status": "warning"},
            ],
        },
        "error": None,
    }
