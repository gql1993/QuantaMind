from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class ClientPreferences:
    profile_id: str
    active_layout_by_target: dict[str, str] = field(default_factory=dict)
    pinned_shortcuts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "active_layout_by_target": dict(self.active_layout_by_target),
            "pinned_shortcuts": list(self.pinned_shortcuts),
            "metadata": dict(self.metadata or {}),
            "updated_at": self.updated_at,
        }


class InMemoryClientPreferencesStore:
    """Shared client preferences store for web/desktop synchronization."""

    def __init__(self) -> None:
        self._items: dict[str, ClientPreferences] = {}

    def get_or_create(self, profile_id: str = "default") -> ClientPreferences:
        normalized = profile_id.strip() or "default"
        item = self._items.get(normalized)
        if item is None:
            item = ClientPreferences(profile_id=normalized)
            self._items[normalized] = item
        return item

    def set_active_layout(self, *, profile_id: str, target: str, layout_id: str) -> ClientPreferences:
        item = self.get_or_create(profile_id)
        item.active_layout_by_target[target.strip().lower() or "web"] = layout_id
        item.updated_at = utc_now_iso()
        return item

    def set_pinned_shortcuts(self, *, profile_id: str, shortcuts: list[str]) -> ClientPreferences:
        item = self.get_or_create(profile_id)
        deduped: list[str] = []
        for shortcut in shortcuts:
            value = shortcut.strip()
            if value and value not in deduped:
                deduped.append(value)
        item.pinned_shortcuts = deduped
        item.updated_at = utc_now_iso()
        return item

    def sync_active_layout(
        self,
        *,
        profile_id: str,
        source_target: str,
        target: str,
    ) -> ClientPreferences:
        item = self.get_or_create(profile_id)
        source_name = source_target.strip().lower() or "web"
        target_name = target.strip().lower() or "desktop"
        layout_id = item.active_layout_by_target.get(source_name)
        if not layout_id:
            raise KeyError(f"source target has no active layout: {source_name}")
        item.active_layout_by_target[target_name] = layout_id
        item.updated_at = utc_now_iso()
        return item
