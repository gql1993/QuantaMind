from __future__ import annotations

from typing import Iterable, List

from quantamind_v2.contracts.context import ContextBundle, ContextLayer
from quantamind_v2.core.context_assembler.budgets import ContextBudget, trim_to_budget


class ContextAssembler:
    """Phase 1 minimal context assembler."""

    def __init__(self, budget: ContextBudget | None = None) -> None:
        self.budget = budget or ContextBudget()

    def assemble(self, layers: Iterable[ContextLayer]) -> ContextBundle:
        selected: List[ContextLayer] = []
        consumed = 0
        for layer in layers:
            content = (layer.content or "").strip()
            if not content:
                continue
            remaining = self.budget.usable_chars - consumed
            if remaining <= 0:
                break
            if len(content) > remaining:
                trimmed = trim_to_budget(content, ContextBudget(max_chars=remaining))
                selected.append(layer.model_copy(update={"content": trimmed}))
                consumed += len(trimmed)
                break
            selected.append(layer)
            consumed += len(content)
        return ContextBundle(layers=selected)

    def to_text(self, bundle: ContextBundle) -> str:
        parts = []
        for layer in bundle.layers:
            parts.append(f"[{layer.layer_type.value}]\n{layer.content}")
        return "\n\n".join(parts).strip()
