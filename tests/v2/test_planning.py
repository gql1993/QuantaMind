from quantamind_v2.core.coordination import CoordinationMode, CoordinationPlanner, CoordinationRouter
from quantamind_v2.core.planning import detect_intent, evaluate_message_heuristics
from quantamind_v2.shortcuts.bootstrap import build_default_shortcut_registry


def test_planning_intent_and_heuristics_for_multi_agent_text():
    intent = detect_intent("请让设计与工艺团队协同分析并给出建议")
    heuristics = evaluate_message_heuristics("请让设计与工艺团队协同分析并给出建议")
    assert intent.intent.value == "multi_agent_analysis"
    assert heuristics.complexity == "high"
    assert "design_specialist" in heuristics.owner_agents


def test_coordination_planner_includes_planning_metadata():
    router = CoordinationRouter(build_default_shortcut_registry())
    route_result = router.route("请发送今天情报")
    planner = CoordinationPlanner()
    plan = planner.build_plan("请发送今天情报", route_result)
    assert plan["mode"] == CoordinationMode.SHORTCUT
    assert "intent" in plan
    assert "heuristics" in plan
    assert "agent_selection" in plan
    assert "scheduling" in plan
    assert plan["steps"][0]["owner_agent"] == "intel_officer"
    assert plan["steps"][0]["kind"] == "shortcut"


def test_planning_heuristics_budget_risk_can_raise_priority():
    heuristics = evaluate_message_heuristics(
        "请分析系统状态",
        priority="normal",
        budget_seconds=10,
    )
    assert heuristics.budget_risk == "high"
    assert heuristics.effective_priority == "high"
