from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class DesktopCard:
    card_id: str
    title: str
    level: str
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DesktopWorkspaceSnapshot:
    timestamp: str = field(default_factory=utc_now_iso)
    gateway_base: str = ""
    health_ok: bool = False
    health_payload: dict[str, Any] = field(default_factory=dict)
    running_runs: int = 0
    failed_runs: int = 0
    running_tasks: int = 0
    pending_approvals: int = 0
    artifacts_total: int = 0
    active_layout_id: str = ""
    active_layout_name: str = ""
    active_panels: list[str] = field(default_factory=list)
    cards: list[DesktopCard] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["cards"] = [card.to_dict() for card in self.cards]
        return payload
