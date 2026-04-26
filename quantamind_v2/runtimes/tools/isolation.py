from __future__ import annotations

from quantamind_v2.contracts.tool import ToolClass
from quantamind_v2.runtimes.tools.classes import DEFAULT_TOOL_PROFILES, ToolExecutionProfile


class ToolIsolationResolver:
    """Resolve default execution profile from a tool class."""

    def resolve(self, tool_class: ToolClass) -> ToolExecutionProfile:
        try:
            return DEFAULT_TOOL_PROFILES[tool_class]
        except KeyError as exc:
            raise ValueError(f"unsupported tool class: {tool_class}") from exc
