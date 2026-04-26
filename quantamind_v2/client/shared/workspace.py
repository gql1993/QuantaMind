from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.contracts.run import utc_now_iso


@dataclass(slots=True)
class WorkspacePanel:
    panel_id: str
    title: str
    order: int
    visible: bool = True
    source: str = "shared_state"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "order": self.order,
            "visible": self.visible,
            "source": self.source,
            "metadata": dict(self.metadata or {}),
        }


@dataclass(slots=True)
class WorkspaceLayout:
    layout_id: str
    name: str
    target: str = "web"
    panels: list[WorkspacePanel] = field(default_factory=list)
    is_builtin: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "name": self.name,
            "target": self.target,
            "panels": [panel.to_dict() for panel in sorted(self.panels, key=lambda item: item.order)],
            "is_builtin": self.is_builtin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class InMemoryWorkspaceLayoutStore:
    """Shared workspace layouts for web/desktop shells."""

    def __init__(self) -> None:
        self._layouts: dict[str, WorkspaceLayout] = {}
        self._active_by_target: dict[str, str] = {}
        self._bootstrap_builtin_layouts()

    def _bootstrap_builtin_layouts(self) -> None:
        web = WorkspaceLayout(
            layout_id="layout-web-default",
            name="Web Default",
            target="web",
            is_builtin=True,
            panels=[
                WorkspacePanel(panel_id="run-console", title="Run Console", order=1),
                WorkspacePanel(panel_id="task-center", title="Task Center", order=2),
                WorkspacePanel(panel_id="artifact-viewer", title="Artifact Viewer", order=3),
                WorkspacePanel(panel_id="approval-center", title="Approval Center", order=4),
            ],
        )
        desktop = WorkspaceLayout(
            layout_id="layout-desktop-default",
            name="Desktop Default",
            target="desktop",
            is_builtin=True,
            panels=[
                WorkspacePanel(panel_id="health", title="Gateway Health", order=1),
                WorkspacePanel(panel_id="runs", title="Runs", order=2),
                WorkspacePanel(panel_id="tasks", title="Tasks", order=3),
                WorkspacePanel(panel_id="approvals", title="Approvals", order=4),
                WorkspacePanel(panel_id="artifacts", title="Artifacts", order=5),
            ],
        )
        self._layouts[web.layout_id] = web
        self._layouts[desktop.layout_id] = desktop
        self._active_by_target["web"] = web.layout_id
        self._active_by_target["desktop"] = desktop.layout_id

    def list_layouts(self, *, target: str | None = None) -> list[WorkspaceLayout]:
        items = list(self._layouts.values())
        if target:
            normalized = target.strip().lower()
            items = [item for item in items if item.target == normalized]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def get_layout(self, layout_id: str) -> WorkspaceLayout | None:
        return self._layouts.get(layout_id)

    def save_layout(self, layout: WorkspaceLayout, *, replace: bool = False) -> WorkspaceLayout:
        layout_id = layout.layout_id.strip()
        if not layout_id:
            raise ValueError("layout_id cannot be empty")
        if layout_id in self._layouts and not replace:
            raise ValueError(f"layout already exists: {layout_id}")
        layout.layout_id = layout_id
        layout.target = (layout.target or "web").strip().lower()
        layout.updated_at = utc_now_iso()
        if not layout.created_at:
            layout.created_at = layout.updated_at
        self._layouts[layout.layout_id] = layout
        if self._active_by_target.get(layout.target) is None:
            self._active_by_target[layout.target] = layout.layout_id
        return layout

    def activate_layout(self, layout_id: str, *, target: str | None = None) -> WorkspaceLayout:
        layout = self.get_layout(layout_id)
        if layout is None:
            raise KeyError(f"layout not found: {layout_id}")
        target_name = (target or layout.target).strip().lower()
        self._active_by_target[target_name] = layout.layout_id
        return layout

    def get_active_layout(self, *, target: str = "web") -> WorkspaceLayout | None:
        target_name = target.strip().lower() or "web"
        layout_id = self._active_by_target.get(target_name)
        if layout_id is None:
            return None
        return self._layouts.get(layout_id)
