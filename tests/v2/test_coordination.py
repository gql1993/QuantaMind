from quantamind_v2.core.coordination import (
    CoordinationConflictStrategy,
    CoordinationAuditStore,
    CoordinationDelegator,
    CoordinationMerger,
    CoordinationMode,
    CoordinationPlanner,
    CoordinationPolicies,
    CoordinationRouter,
    CoordinationSupervisor,
    decide_coordination_conflict,
    detect_active_coordination_conflict,
)
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.shortcuts.bootstrap import build_default_shortcut_registry


def test_coordination_router_matches_shortcut():
    router = CoordinationRouter(build_default_shortcut_registry())
    result = router.route("请发送今天情报")
    assert result["mode"] == CoordinationMode.SHORTCUT
    assert result["shortcut"].name == "intel_today"


def test_coordination_router_detects_multi_agent_plan():
    router = CoordinationRouter(build_default_shortcut_registry())
    result = router.route("请让设计与工艺团队协同分析这个问题")
    assert result["mode"] == CoordinationMode.MULTI_AGENT_PLAN


def test_coordination_planner_builds_shortcut_plan():
    router = CoordinationRouter(build_default_shortcut_registry())
    route_result = router.route("请发送今天情报")
    planner = CoordinationPlanner()
    plan = planner.build_plan("请发送今天情报", route_result)
    assert plan["mode"] == CoordinationMode.SHORTCUT
    assert plan["steps"][0]["kind"] == "shortcut"


def test_coordination_merger_combines_summaries():
    merger = CoordinationMerger()
    result = merger.merge(
        [
            {"summary": "设计团队已完成初步分析"},
            {"status_message": "工艺团队已给出风险点评估"},
        ]
    )
    assert result["count"] == 2
    assert "设计团队已完成初步分析" in result["summary"]
    assert "工艺团队已给出风险点评估" in result["summary"]


def test_coordination_delegator_creates_child_runs_and_topology():
    coordinator = RunCoordinator()
    parent = coordinator.create_run(RunType.CHAT, owner_agent="planner")
    router = CoordinationRouter(build_default_shortcut_registry())
    route_result = router.route("请让设计与工艺团队协同分析这个问题")
    planner = CoordinationPlanner()
    plan = planner.build_plan("请让设计与工艺团队协同分析这个问题", route_result)
    delegator = CoordinationDelegator(coordinator)

    result = delegator.delegate_plan(parent.run_id, plan)

    assert result["parent_run"].metadata["coordination_topology"]["root_run_id"] == parent.run_id
    assert len(result["child_runs"]) == 2
    assert len(result["topology"].nodes) == 2
    assert result["topology"].nodes[1].depends_on == [result["topology"].nodes[0].node_id]


def test_coordination_supervisor_executes_multi_agent_plan():
    coordinator = RunCoordinator()
    parent = coordinator.create_run(RunType.CHAT, owner_agent="coordinator")
    router = CoordinationRouter(build_default_shortcut_registry())
    planner = CoordinationPlanner()
    delegator = CoordinationDelegator(coordinator)
    merger = CoordinationMerger()
    supervisor = CoordinationSupervisor(
        coordinator=coordinator,
        router=router,
        planner=planner,
        delegator=delegator,
        merger=merger,
        policies=CoordinationPolicies(),
    )

    result = supervisor.execute(parent.run_id, "请让设计与工艺团队协同分析这个问题")

    assert result["run"].state.value == "completed"
    assert result["route_result"]["mode"] == CoordinationMode.MULTI_AGENT_PLAN
    assert len(result["delegated"]["child_runs"]) == 2
    assert result["merged"]["count"] == 2


def test_coordination_conflict_decision_variants():
    coordinator = RunCoordinator()
    active = coordinator.create_run(RunType.CHAT, owner_agent="coordinator")
    coordinator.update_run(active.run_id, metadata={"profile_id": "alice", "coordination_role": "root"})
    coordinator.transition(active.run_id, RunState.RUNNING, stage="running", status_message="running")
    conflict = detect_active_coordination_conflict(profile_id="alice", runs=coordinator.list_runs())
    assert conflict is not None
    assert conflict.run_id == active.run_id

    queue = decide_coordination_conflict(strategy=CoordinationConflictStrategy.QUEUE, conflict_run=conflict)
    assert queue.should_queue is True
    assert queue.should_reject is False

    reject = decide_coordination_conflict(strategy=CoordinationConflictStrategy.REJECT, conflict_run=conflict)
    assert reject.should_reject is True
    assert reject.should_queue is False

    degrade = decide_coordination_conflict(
        strategy=CoordinationConflictStrategy.DEGRADE_SINGLE_AGENT,
        conflict_run=conflict,
    )
    assert degrade.should_degrade_single_agent is True


def test_coordination_audit_store_filters():
    store = CoordinationAuditStore()
    store.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="reject",
        outcome="rejected",
        reason="conflict",
    )
    store.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="conflict",
    )
    store.append(
        event_type="coordination_conflict_decided",
        profile_id="bob",
        strategy="degrade_single_agent",
        outcome="degraded_single_agent",
        reason="conflict",
    )
    alice_items = store.list_events(profile_id="alice")
    assert len(alice_items) == 2
    queued_items = store.list_events(profile_id="alice", outcome="queued")
    assert len(queued_items) == 1
    assert queued_items[0].strategy == "queue"


def test_coordination_audit_store_retention_limit():
    store = CoordinationAuditStore(max_items=100)
    for idx in range(120):
        store.append(
            event_type="coordination_conflict_decided",
            profile_id="alice",
            strategy="queue",
            outcome="queued",
            reason=f"conflict-{idx}",
        )
    items = store.list_events(profile_id="alice", limit=200)
    assert len(items) == 100
    reasons = {item.reason for item in items}
    assert "conflict-0" not in reasons
    assert "conflict-119" in reasons
