"""
将 QEDA 工程层迁移工具（client.qeda_bridge）接入 QuantumHands。

占位 handler 由 QEDAToolRegistry 管理；此处仅做注册与能力发现。
"""

from __future__ import annotations

from typing import Any, Dict, List

from quantamind.client.qeda_bridge.tool_registry import QEDAToolRegistry, create_default_registry

_registry: QEDAToolRegistry | None = None


def get_qeda_bridge_registry() -> QEDAToolRegistry:
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry


def qeda_bridge_capabilities() -> Dict[str, Any]:
    """列出 QEDA 桥接工具注册表（占位实现），供 Agent 发现能力。"""
    reg = get_qeda_bridge_registry()
    tools: List[Dict[str, Any]] = []
    for r in reg.get_registrations():
        tools.append(
            {
                "name": r.name,
                "description": r.description,
                "category": r.category,
                "requires_approval": r.requires_approval,
            }
        )
    return {
        "source": "qeda_bridge",
        "count": reg.count,
        "tools": tools,
    }


def _make_bridge_handler(reg: QEDAToolRegistry, tool_name: str):
    async def _bridge_handler(**kwargs: Any) -> Any:
        return await reg.execute(tool_name, **kwargs)

    return _bridge_handler


def register_qeda_bridge_tools() -> None:
    """将桥接注册表中的工具全部挂到 hands.TOOL_REGISTRY。"""
    from quantamind.server import hands as h

    reg = get_qeda_bridge_registry()

    h.register_tool(
        "qeda_bridge_capabilities",
        "QEDA 桥: 列出迁移自 QEDA 工程层的占位工具（设计/仿真/优化/导出）及元数据",
        qeda_bridge_capabilities,
    )

    for r in reg.get_registrations():
        h.register_tool(r.name, f"QEDA 桥: {r.description}", _make_bridge_handler(reg, r.name))
