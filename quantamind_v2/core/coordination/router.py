from __future__ import annotations

from enum import Enum

from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


class CoordinationMode(str, Enum):
    SINGLE_AGENT = "single_agent"
    SHORTCUT = "shortcut"
    MULTI_AGENT_PLAN = "multi_agent_plan"


class CoordinationRouter:
    """Phase 1 minimal routing for V2 coordination."""

    def __init__(self, shortcut_registry: ShortcutRegistry) -> None:
        self.shortcut_registry = shortcut_registry

    def route(self, message: str) -> dict:
        shortcut = self.shortcut_registry.match(message)
        if shortcut is not None:
            return {
                "mode": CoordinationMode.SHORTCUT,
                "shortcut": shortcut,
                "reason": f"matched shortcut `{shortcut.name}`",
            }

        text = (message or "").strip().lower()
        multi_agent_terms = (
            "协同",
            "联合",
            "一起分析",
            "多智能体",
            "跨团队",
            "设计和工艺",
            "设计与工艺",
            "仿真和测控",
            "仿真与测控",
        )
        if any(term in text for term in multi_agent_terms):
            return {
                "mode": CoordinationMode.MULTI_AGENT_PLAN,
                "shortcut": None,
                "reason": "message suggests multi-agent planning",
            }

        return {
            "mode": CoordinationMode.SINGLE_AGENT,
            "shortcut": None,
            "reason": "default single-agent path",
        }
