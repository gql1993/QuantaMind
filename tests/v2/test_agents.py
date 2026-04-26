from quantamind_v2.agents import AgentPolicyEngine, build_default_agent_registry


def test_default_agent_registry_contains_core_profiles():
    registry = build_default_agent_registry()
    assert registry.has("intel_officer")
    assert registry.has("planner")
    assert registry.has("assistant")
    intel = registry.get("intel_officer")
    assert intel is not None
    assert "intel_digest" in intel.capabilities


def test_agent_policy_selects_multi_agent_pair():
    registry = build_default_agent_registry()
    policy = AgentPolicyEngine(registry)
    result = policy.select_agents(
        route_mode="multi_agent_plan",
        shortcut_owner=None,
        heuristic_owner_agents=["design_specialist"],
    )
    assert result.primary_agent == "design_specialist"
    assert len(result.selected_agents) >= 2
