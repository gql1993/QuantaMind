from quantamind_v2.client.shared import InMemoryWorkspaceLayoutStore, WorkspaceLayout, WorkspacePanel


def test_workspace_layout_store_has_builtin_layouts():
    store = InMemoryWorkspaceLayoutStore()
    web = store.get_active_layout(target="web")
    desktop = store.get_active_layout(target="desktop")
    assert web is not None
    assert desktop is not None
    assert web.layout_id.startswith("layout-web")
    assert desktop.layout_id.startswith("layout-desktop")


def test_workspace_layout_store_create_and_activate():
    store = InMemoryWorkspaceLayoutStore()
    layout = WorkspaceLayout(
        layout_id="layout-web-test",
        name="Web Test",
        target="web",
        panels=[WorkspacePanel(panel_id="run-console", title="Run Console", order=1)],
    )
    stored = store.save_layout(layout)
    assert stored.layout_id == "layout-web-test"
    activated = store.activate_layout("layout-web-test", target="web")
    assert activated.layout_id == "layout-web-test"
    assert store.get_active_layout(target="web").layout_id == "layout-web-test"
