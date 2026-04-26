from quantamind_v2.client.shared import InMemoryWorkspaceRecoveryStore


def test_workspace_recovery_store_create_list_latest():
    store = InMemoryWorkspaceRecoveryStore()
    p1 = store.create(profile_id="alice", target="web", layout_id="layout-web-default", run_id="run-1")
    p2 = store.create(profile_id="alice", target="web", layout_id="layout-web-default", run_id="run-2")
    assert p1.point_id != p2.point_id
    items = store.list(profile_id="alice", target="web", limit=10)
    assert len(items) == 2
    assert items[0].run_id == "run-2"
    latest = store.latest(profile_id="alice", target="web")
    assert latest is not None
    assert latest.run_id == "run-2"
