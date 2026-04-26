from quantamind_v2.client.desktop import DesktopWorkspaceShell


class _FakeDesktopShell(DesktopWorkspaceShell):
    def __init__(self, responses: dict[str, tuple[int, dict]], **kwargs):
        super().__init__("http://fake.local", **kwargs)
        self._responses = responses

    def _get_json(self, path: str):  # type: ignore[override]
        return self._responses.get(path, (404, {}))


def test_desktop_shell_uses_active_layout_panels():
    responses = {
        "/health": (200, {"status": "ok"}),
        "/api/v2/client/workspace/snapshot?target=desktop": (
            200,
            {
                "layout": {
                    "layout_id": "layout-desktop-custom",
                    "name": "Custom Desktop",
                    "panels": [
                        {"panel_id": "runs", "title": "Runs", "order": 1},
                        {"panel_id": "tasks", "title": "Tasks", "order": 2},
                        {"panel_id": "custom", "title": "Custom Panel", "order": 3},
                    ],
                },
                "state": {"summary": {"run_running": 2, "run_failed": 1, "task_running": 3, "artifact_total": 8}},
            },
        ),
        "/api/v2/client/shared/state": (200, {"state": {"summary": {"run_running": 2, "run_failed": 1, "task_running": 3, "artifact_total": 8}}}),
        "/api/v2/approvals?status=pending": (200, {"items": [{"approval_id": "a1"}]}),
    }
    shell = _FakeDesktopShell(responses)
    snapshot = shell.collect_snapshot()
    assert snapshot.active_layout_id == "layout-desktop-custom"
    assert snapshot.active_layout_name == "Custom Desktop"
    assert snapshot.active_panels == ["runs", "tasks", "custom"]
    assert [card.card_id for card in snapshot.cards] == ["runs", "tasks", "custom"]
    assert snapshot.cards[0].metadata["refresh_interval_seconds"] == 5
    assert snapshot.cards[2].summary == "custom panel"


def test_desktop_shell_panel_refresh_override():
    responses = {
        "/health": (200, {"status": "ok"}),
        "/api/v2/client/workspace/snapshot?target=desktop": (
            200,
            {
                "layout": {
                    "layout_id": "layout-desktop-default",
                    "name": "Default Desktop",
                    "panels": [{"panel_id": "runs", "title": "Runs", "order": 1}],
                },
                "state": {"summary": {"run_running": 1, "run_failed": 0, "task_running": 0, "artifact_total": 0}},
            },
        ),
        "/api/v2/client/shared/state": (200, {"state": {"summary": {"run_running": 1}}}),
        "/api/v2/approvals?status=pending": (200, {"items": []}),
    }
    shell = _FakeDesktopShell(responses, panel_refresh_overrides={"runs": 2})
    snapshot = shell.collect_snapshot()
    assert snapshot.cards[0].card_id == "runs"
    assert snapshot.cards[0].metadata["refresh_interval_seconds"] == 2
