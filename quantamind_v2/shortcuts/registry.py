from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from quantamind_v2.contracts.run import RunType


@dataclass(slots=True)
class ShortcutDefinition:
    name: str
    description: str
    handler: Callable[..., object]
    triggers: List[str] = field(default_factory=list)
    run_type: RunType = RunType.SYSTEM
    owner_agent: Optional[str] = None


class ShortcutRegistry:
    """Phase 1 minimal shortcut registry."""

    def __init__(self) -> None:
        self._items: Dict[str, ShortcutDefinition] = {}

    def register(self, definition: ShortcutDefinition) -> None:
        self._items[definition.name] = definition

    def get(self, name: str) -> Optional[ShortcutDefinition]:
        return self._items.get(name)

    def list(self) -> List[ShortcutDefinition]:
        return list(self._items.values())

    def match(self, message: str) -> Optional[ShortcutDefinition]:
        normalized = (message or "").strip().lower()
        for item in self._items.values():
            if item.name.lower() == normalized:
                return item
            if any(trigger.lower() in normalized for trigger in item.triggers):
                return item
        return None
