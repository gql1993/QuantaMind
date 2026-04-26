from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from quantamind_v2.config import AppSettings
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.shortcuts.bootstrap import build_default_shortcut_registry


def test_v2_gateway_coordination_execute_multi_agent_plan():
    client = TestClient(create_app(shortcut_registry=build_default_shortcut_registry()))
    response = client.post(
        "/api/v2/coordination/execute",
        json={"message": "请让设计与工艺团队协同分析这个问题", "origin": "test"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_result"]["mode"] == "multi_agent_plan"
    assert payload["run"]["state"] == "completed"
    assert len(payload["delegated"]["child_runs"]) == 2
    assert payload["delegated"]["topology"]["root_run_id"] == payload["run"]["run_id"]
    assert len(payload["run"]["artifacts"]) == 1
    artifact_id = payload["run"]["artifacts"][0]
    assert artifact_id.startswith("artifact-")

    artifact_response = client.get(f"/api/v2/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["run_id"] == payload["run"]["run_id"]
    assert artifact["artifact_type"] == "coordination_report"
    assert artifact["title"] == "coordination merged result"
    assert artifact["payload"]["merged"]["count"] == 2

    view_response = client.get(f"/api/v2/artifacts/{artifact_id}/view")
    assert view_response.status_code == 200
    view = view_response.json()
    assert view["artifact_type"] == "coordination_report"
    assert "## Coordination" in view["content"]
    assert "## Child Outputs" in view["content"]

    run_artifacts_response = client.get(f"/api/v2/runs/{payload['run']['run_id']}/artifacts")
    assert run_artifacts_response.status_code == 200
    run_artifacts = run_artifacts_response.json()["items"]
    assert len(run_artifacts) == 1
    assert run_artifacts[0]["artifact_id"] == artifact_id


def test_gateway_coordination_conflict_reject_and_queue():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "alice", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry()))

    reject_resp = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "alice",
            "conflict_strategy": "reject",
        },
    )
    assert reject_resp.status_code == 409
    detail = reject_resp.json()["detail"]
    assert detail["conflict_run_id"] == active.run_id
    assert detail["strategy"] == "reject"

    queue_resp = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "alice",
            "conflict_strategy": "queue",
        },
    )
    assert queue_resp.status_code == 200
    payload = queue_resp.json()
    assert payload["queued"] is True
    assert payload["run"]["state"] == "queued"
    assert payload["run"]["stage"] == "coordination_queued_conflict"
    assert payload["conflict"]["conflict_run_id"] == active.run_id


def test_gateway_coordination_conflict_can_degrade_to_single_agent():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "alice", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry()))

    response = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "alice",
            "conflict_strategy": "degrade_single_agent",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] is False
    assert payload["route_result"]["mode"] == "single_agent"
    assert payload["plan"]["mode"] == "single_agent"
    assert payload["conflict"]["should_degrade_single_agent"] is True


def test_gateway_coordination_audit_events_and_export():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "audit_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry()))

    reject_resp = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "audit_user",
            "conflict_strategy": "reject",
        },
    )
    assert reject_resp.status_code == 409

    queue_resp = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "audit_user",
            "conflict_strategy": "queue",
        },
    )
    assert queue_resp.status_code == 200
    assert queue_resp.json()["queued"] is True

    degrade_resp = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "audit_user",
            "conflict_strategy": "degrade_single_agent",
        },
    )
    assert degrade_resp.status_code == 200
    assert degrade_resp.json()["route_result"]["mode"] == "single_agent"

    events_resp = client.get("/api/v2/coordination/audit/events?profile_id=audit_user")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    outcomes = {item["outcome"] for item in events}
    assert "rejected" in outcomes
    assert "queued" in outcomes
    assert "degraded_single_agent" in outcomes
    assert all(item["event_id"].startswith("caev-") for item in events)

    export_resp = client.get("/api/v2/coordination/audit/export?profile_id=audit_user&outcome=queued")
    assert export_resp.status_code == 200
    exported = export_resp.json()
    assert exported["summary"]["total"] >= 1
    assert all(item["outcome"] == "queued" for item in exported["items"])


def test_gateway_coordination_uses_default_conflict_strategy_from_settings():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "default_strategy_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    settings = AppSettings.from_dict({"coordination": {"default_conflict_strategy": "queue"}})
    client = TestClient(
        create_app(
            coordinator=coordinator,
            shortcut_registry=build_default_shortcut_registry(),
            settings=settings,
        )
    )
    response = client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "default_strategy_user",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] is True
    assert payload["conflict"]["strategy"] == "queue"


def test_gateway_coordination_audit_export_limit_is_capped_by_settings():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "limit_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    settings = AppSettings.from_dict({"coordination": {"audit_export_limit_max": 2}})
    client = TestClient(
        create_app(
            coordinator=coordinator,
            shortcut_registry=build_default_shortcut_registry(),
            settings=settings,
        )
    )
    for strategy in ("reject", "queue", "degrade_single_agent"):
        client.post(
            "/api/v2/coordination/execute",
            json={
                "message": "请让设计与工艺团队协同分析这个问题",
                "origin": "test",
                "profile_id": "limit_user",
                "conflict_strategy": strategy,
            },
        )
    export_resp = client.get("/api/v2/coordination/audit/export?profile_id=limit_user&limit=999")
    assert export_resp.status_code == 200
    exported = export_resp.json()
    assert exported["summary"]["effective_limit"] == 2
    assert exported["summary"]["configured_export_limit_max"] == 2
    assert len(exported["items"]) <= 2


def test_gateway_coordination_policy_endpoint_and_persistence_across_apps(tmp_path):
    state_dir = str(tmp_path / "coordination-state")
    settings = AppSettings.from_dict(
        {
            "coordination": {
                "default_conflict_strategy": "degrade_single_agent",
                "state_dir": state_dir,
            }
        }
    )
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "persist_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")

    client_a = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry(), settings=settings))
    set_resp = client_a.post(
        "/api/v2/coordination/policies/conflict-strategy",
        json={"profile_id": "persist_user", "strategy": "queue", "source": "test"},
    )
    assert set_resp.status_code == 200
    get_resp = client_a.get("/api/v2/coordination/policies/conflict-strategy?profile_id=persist_user")
    assert get_resp.status_code == 200
    assert get_resp.json()["strategy"] == "queue"

    # Create a second app instance using the same persisted state dir.
    client_b = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry(), settings=settings))
    execute_resp = client_b.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "persist_user",
        },
    )
    assert execute_resp.status_code == 200
    payload = execute_resp.json()
    assert payload["queued"] is True
    assert payload["conflict_strategy_source"] == "policy_override"


def test_gateway_coordination_persistence_health_endpoint_reports_recovery(tmp_path: Path):
    state_dir = tmp_path / "coordination-health"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "coordination_audit.jsonl").write_text("bad-json-line\n", encoding="utf-8")
    (state_dir / "coordination_policy.json").write_text("{broken", encoding="utf-8")
    settings = AppSettings.from_dict({"coordination": {"state_dir": str(state_dir)}})
    client = TestClient(create_app(shortcut_registry=build_default_shortcut_registry(), settings=settings))
    response = client.get("/api/v2/coordination/persistence/health")
    assert response.status_code == 200
    payload = response.json()
    assert "audit" in payload
    assert "policy" in payload
    assert payload["audit"]["status"] in {"ok", "recovered", "warn"}
    assert payload["policy"]["status"] in {"ok", "recovered", "warn"}


def test_gateway_coordination_persistence_archives_and_migration_plan_endpoints(tmp_path: Path):
    state_dir = str(tmp_path / "coordination-archives")
    settings = AppSettings.from_dict(
        {
            "coordination": {
                "state_dir": state_dir,
                "audit_rotate_max_bytes": 1,
                "audit_rotate_interval_seconds": 3600,
                "database_read_profile_allowlist": ["archive_user"],
                "database_read_rollout_percentage": 10,
            }
        }
    )
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "archive_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry(), settings=settings))
    client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "archive_user",
            "conflict_strategy": "queue",
        },
    )
    archives_resp = client.get("/api/v2/coordination/persistence/archives?limit=20")
    assert archives_resp.status_code == 200
    archives = archives_resp.json()["items"]
    assert len(archives) >= 1
    assert any(item["reason"] in {"size", "time"} for item in archives)

    migration_resp = client.get("/api/v2/coordination/persistence/migration-plan")
    assert migration_resp.status_code == 200
    migration = migration_resp.json()
    assert migration["status"] == "draft"
    assert migration["target"] == "database-backed coordination persistence"
    assert len(migration["phases"]) >= 3
    assert migration["current_state"]["database_read_profile_allowlist"] == ["archive_user"]
    assert migration["current_state"]["database_read_rollout_percentage"] == 10


def test_gateway_coordination_persistence_dashboard_endpoint(tmp_path: Path):
    state_dir = str(tmp_path / "coordination-dashboard")
    db_path = str(Path(state_dir) / "coordination.db")
    settings = AppSettings.from_dict(
        {
            "coordination": {
                "state_dir": state_dir,
                "database_path": db_path,
                "audit_rotate_max_bytes": 1,
                "audit_rotate_interval_seconds": 3600,
                "database_read_rollout_percentage": 20,
                "dual_write_enabled": True,
                "database_read_preferred": True,
                "database_read_fallback_to_file": True,
                "database_read_profile_allowlist": ["dashboard_user"],
            }
        }
    )
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "dashboard_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry(), settings=settings))
    client.post(
        "/api/v2/coordination/execute",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "origin": "test",
            "profile_id": "dashboard_user",
            "conflict_strategy": "queue",
        },
    )
    client.post(
        "/api/v2/coordination/policies/conflict-strategy",
        json={"profile_id": "dashboard_user", "strategy": "queue", "source": "dashboard-test"},
    )
    client.get("/api/v2/coordination/persistence/cutover/drill?profile_id=dashboard_user&window_limit=20")
    client.get(
        "/api/v2/coordination/persistence/cutover/drill?profile_id=dashboard_user&window_limit=20&simulate_secondary_failure=true"
    )
    response = client.get("/api/v2/coordination/persistence/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "metrics" in payload
    assert "alerts" in payload
    assert "thresholds" in payload
    assert payload["metrics"]["audit"]["max_size_bytes"] == 1
    assert payload["metrics"]["archive"]["total"] >= 1
    assert payload["thresholds"]["database_read_rollout_percentage"] == 20
    assert payload["metrics"]["cutover"]["fallback_anomaly_count"] >= 2
    assert payload["metrics"]["cutover"]["database_coverage_ratio"] >= 0
    assert payload["metrics"]["cutover"]["audit"]["tracked_profiles_total"] >= 1
    assert payload["metrics"]["cutover"]["controls"]["audit"]["profile_allowlist"] == ["dashboard_user"]
    assert any(
        item["profile_id"] == "dashboard_user"
        for item in payload["metrics"]["cutover"]["audit"]["profile_hits"]
    )
    assert any(alert["type"] == "cutover_fallback" for alert in payload["alerts"])


def test_gateway_coordination_persistence_consistency_requires_dual_write():
    client = TestClient(create_app(shortcut_registry=build_default_shortcut_registry()))
    response = client.get("/api/v2/coordination/persistence/consistency")
    assert response.status_code == 400

    drill_response = client.get("/api/v2/coordination/persistence/cutover/drill")
    assert drill_response.status_code == 400

    controls_response = client.get("/api/v2/coordination/persistence/cutover/controls")
    assert controls_response.status_code == 400


def test_gateway_coordination_dual_write_baseline_persists_to_sqlite(tmp_path: Path):
    state_dir = tmp_path / "coordination-dualwrite"
    db_path = state_dir / "coordination.db"
    settings = AppSettings.from_dict(
        {
            "coordination": {
                "state_dir": str(state_dir),
                "database_path": str(db_path),
                "dual_write_enabled": True,
                "database_read_preferred": True,
                "database_read_fallback_to_file": True,
                "database_read_profile_allowlist": ["dw_user"],
                "database_read_rollout_percentage": 50,
            }
        }
    )
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, origin="seed", owner_agent="coordinator", status_message="active")
    coordinator.update_run(active.run_id, metadata={"profile_id": "dw_user", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="still running")
    client = TestClient(create_app(coordinator=coordinator, shortcut_registry=build_default_shortcut_registry(), settings=settings))

    set_resp = client.post(
        "/api/v2/coordination/policies/conflict-strategy",
        json={"profile_id": "dw_user", "strategy": "queue", "source": "dualwrite-test"},
    )
    assert set_resp.status_code == 200

    execute_resp = client.post(
        "/api/v2/coordination/execute",
        json={"message": "请让设计与工艺团队协同分析这个问题", "origin": "test", "profile_id": "dw_user"},
    )
    assert execute_resp.status_code == 200
    assert execute_resp.json()["queued"] is True

    with sqlite3.connect(str(db_path)) as conn:
        policy_rows = conn.execute("SELECT COUNT(1) FROM coordination_conflict_policies WHERE profile_id = ?", ("dw_user",)).fetchone()[0]
        audit_rows = conn.execute("SELECT COUNT(1) FROM coordination_audit_events WHERE profile_id = ?", ("dw_user",)).fetchone()[0]
    assert policy_rows >= 1
    assert audit_rows >= 1

    consistency_resp = client.get("/api/v2/coordination/persistence/consistency?profile_id=dw_user&window_limit=100")
    assert consistency_resp.status_code == 200
    consistency = consistency_resp.json()
    assert consistency["status"] == "consistent"
    assert consistency["reports"]["audit"]["difference_count"] == 0
    assert consistency["reports"]["policy"]["difference_count"] == 0

    cutover_ok = client.get("/api/v2/coordination/persistence/cutover/drill?profile_id=dw_user&window_limit=20")
    assert cutover_ok.status_code == 200
    ok_payload = cutover_ok.json()
    assert ok_payload["status"] == "ok"
    assert ok_payload["reports"]["audit"]["selected_backend"] == "secondary_sqlite"
    assert ok_payload["reports"]["policy"]["selected_backend"] == "secondary_sqlite"
    assert ok_payload["reports"]["audit"]["routing_reason"] == "allowlist"
    assert ok_payload["reports"]["policy"]["routing_reason"] == "allowlist"

    cutover_fail = client.get(
        "/api/v2/coordination/persistence/cutover/drill?profile_id=dw_user&window_limit=20&simulate_secondary_failure=true"
    )
    assert cutover_fail.status_code == 200
    fail_payload = cutover_fail.json()
    assert fail_payload["status"] == "degraded"
    assert fail_payload["reports"]["audit"]["selected_backend"] == "primary_file_fallback"
    assert fail_payload["reports"]["policy"]["selected_backend"] == "primary_file_fallback"

    rollout_execute_resp = client.post(
        "/api/v2/coordination/policies/conflict-strategy",
        json={"profile_id": "rollout_user", "strategy": "reject", "source": "dualwrite-test"},
    )
    assert rollout_execute_resp.status_code == 200
    rollout_drill = client.get("/api/v2/coordination/persistence/cutover/drill?profile_id=rollout_user&window_limit=20")
    assert rollout_drill.status_code == 200
    rollout_payload = rollout_drill.json()
    rollout_bucket = int(rollout_payload["reports"]["policy"]["rollout_bucket"])
    if rollout_bucket < 50:
        assert rollout_payload["reports"]["policy"]["selected_backend"] == "secondary_sqlite"
        assert rollout_payload["reports"]["policy"]["routing_reason"] == "rollout_percentage"
    else:
        assert rollout_payload["reports"]["policy"]["selected_backend"] == "primary_file"
        assert rollout_payload["reports"]["policy"]["routing_reason"] == "rollout_excluded"

    controls_resp = client.get("/api/v2/coordination/persistence/cutover/controls")
    assert controls_resp.status_code == 200
    controls = controls_resp.json()
    assert controls["audit"]["profile_allowlist"] == ["dw_user"]
    assert controls["audit"]["rollout_percentage"] == 50

    update_controls_resp = client.post(
        "/api/v2/coordination/persistence/cutover/controls",
        json={"profile_allowlist": ["rollout_user"], "rollout_percentage": 100, "source": "runtime-api"},
    )
    assert update_controls_resp.status_code == 200
    updated_controls = update_controls_resp.json()
    assert updated_controls["audit"]["profile_allowlist"] == ["rollout_user"]
    assert updated_controls["audit"]["rollout_percentage"] == 100
    assert updated_controls["audit"]["source"] == "runtime-api"

    updated_drill = client.get("/api/v2/coordination/persistence/cutover/drill?profile_id=rollout_user&window_limit=20")
    assert updated_drill.status_code == 200
    updated_payload = updated_drill.json()
    assert updated_payload["reports"]["policy"]["selected_backend"] == "secondary_sqlite"
    assert updated_payload["reports"]["policy"]["routing_reason"] == "allowlist"
