from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


KNOWLEDGE_ITEMS = [
    {
        "item_id": "kb-chip-design-rules",
        "title": "超导量子芯片设计规则",
        "source": "design-rulebook",
        "tags": ["chip", "design", "rules"],
        "summary": "沉淀芯片版图、耦合结构、工艺约束等设计规则。",
        "updated_at": "2026-04-26T08:00:00Z",
    },
    {
        "item_id": "kb-measurement-calibration",
        "title": "测控校准经验库",
        "source": "measurement-lab",
        "tags": ["measurement", "calibration"],
        "summary": "记录测控链路校准、异常排查和实验参数复用经验。",
        "updated_at": "2026-04-25T17:30:00Z",
    },
    {
        "item_id": "kb-project-risk",
        "title": "项目风险与复盘摘要",
        "source": "project-review",
        "tags": ["project", "risk", "review"],
        "summary": "汇总跨角色协作中的风险、阻塞和复盘结论。",
        "updated_at": "2026-04-24T12:10:00Z",
    },
]

MEMORY_ITEMS = [
    {
        "memory_id": "memory-design-preference",
        "scope": "role:chip-designer",
        "content": "芯片设计人员默认优先查看仿真 Run、设计风险和产物归档。",
        "confidence": 0.92,
        "last_used_at": "2026-04-26T08:20:00Z",
    },
    {
        "memory_id": "memory-manager-summary",
        "scope": "role:project-manager",
        "content": "项目经理关注跨角色进度、阻塞任务和阶段汇报摘要。",
        "confidence": 0.88,
        "last_used_at": "2026-04-26T07:50:00Z",
    },
]


@router.get("/items")
def list_knowledge_items() -> dict:
    return {
        "success": True,
        "data": {
            "items": KNOWLEDGE_ITEMS,
            "total": len(KNOWLEDGE_ITEMS),
        },
        "error": None,
    }


@router.get("/memories")
def list_memories() -> dict:
    return {
        "success": True,
        "data": {
            "items": MEMORY_ITEMS,
            "total": len(MEMORY_ITEMS),
        },
        "error": None,
    }
