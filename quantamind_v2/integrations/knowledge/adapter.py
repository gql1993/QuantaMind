from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class KnowledgeEntry:
    entry_id: str
    title: str
    content: str
    source: str = "manual"
    metadata: dict[str, Any] | None = None
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "metadata": dict(self.metadata or {}),
            "created_at": self.created_at,
        }


class KnowledgeAdapter:
    """Minimal in-memory knowledge adapter for V2 integration shell."""

    def __init__(self) -> None:
        self._entries: dict[str, KnowledgeEntry] = {}
        self._counter = 0

    def index(
        self,
        *,
        title: str,
        content: str,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeEntry:
        self._counter += 1
        entry = KnowledgeEntry(
            entry_id=f"kentry-{self._counter:04d}",
            title=title.strip(),
            content=content.strip(),
            source=source,
            metadata=dict(metadata or {}),
            created_at=utc_now_iso(),
        )
        self._entries[entry.entry_id] = entry
        return entry

    def search(self, query: str, *, limit: int = 10) -> list[KnowledgeEntry]:
        normalized = query.strip().lower()
        if not normalized:
            return list(self._entries.values())[: max(limit, 1)]
        matched: list[KnowledgeEntry] = []
        for item in self._entries.values():
            haystack = f"{item.title}\n{item.content}\n{item.source}".lower()
            if normalized in haystack:
                matched.append(item)
            if len(matched) >= max(limit, 1):
                break
        return matched
