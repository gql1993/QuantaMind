from __future__ import annotations

from quantamind_v2.contracts.run import RunType
from quantamind_v2.services.intel_service import run_today_digest_shortcut
from quantamind_v2.services.system_service import get_database_status_summary, get_system_status_summary
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def build_default_shortcut_registry() -> ShortcutRegistry:
    registry = ShortcutRegistry()
    registry.register(
        ShortcutDefinition(
            name="intel_today",
            description="Send today's intel digest using the stable shortcut path.",
            handler=run_today_digest_shortcut,
            triggers=[
                "今天情报",
                "今日情报",
                "今天日报",
                "今日日报",
                "发送今天情报",
                "发送今天日报",
                "发日报",
            ],
            run_type=RunType.DIGEST,
            owner_agent="intel_officer",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="system_status",
            description="Summarize current system status using the stable V1 status interface.",
            handler=get_system_status_summary,
            triggers=[
                "系统状态",
                "当前状态",
                "gateway状态",
                "网关状态",
                "运行状态",
            ],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="db_status",
            description="Summarize current database and resource connectivity using the stable V1 resource status interface.",
            handler=get_database_status_summary,
            triggers=[
                "数据库状态",
                "数据库连接",
                "pgvector状态",
                "设计主库状态",
                "资源状态",
            ],
            run_type=RunType.SYSTEM,
            owner_agent="data_analyst",
        )
    )
    return registry
