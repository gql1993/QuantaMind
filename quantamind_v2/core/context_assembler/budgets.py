from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ContextBudget:
    max_chars: int = 4000
    reserve_chars: int = 0

    @property
    def usable_chars(self) -> int:
        return max(self.max_chars - self.reserve_chars, 0)


def trim_to_budget(text: str, budget: ContextBudget) -> str:
    normalized = (text or "").strip()
    if len(normalized) <= budget.usable_chars:
        return normalized
    if budget.usable_chars <= 3:
        return normalized[: budget.usable_chars]
    return normalized[: budget.usable_chars - 3].rstrip() + "..."
