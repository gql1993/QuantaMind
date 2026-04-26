from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeLimits:
    default_task_timeout_seconds: float = 20.0
    default_model_timeout_seconds: float = 15.0
    default_mcp_timeout_seconds: float = 10.0
    default_prompt_budget_chars: int = 12000

    def to_dict(self) -> dict:
        return {
            "default_task_timeout_seconds": self.default_task_timeout_seconds,
            "default_model_timeout_seconds": self.default_model_timeout_seconds,
            "default_mcp_timeout_seconds": self.default_mcp_timeout_seconds,
            "default_prompt_budget_chars": self.default_prompt_budget_chars,
        }
