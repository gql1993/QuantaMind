from quantamind_v2.core.context_assembler import (
    ContextAssembler,
    ContextBudget,
    agent_identity_layer,
    project_memory_layer,
    recent_conversation_layer,
    system_layer,
    trim_to_budget,
)


def test_trim_to_budget_shortens_text():
    budget = ContextBudget(max_chars=10)
    result = trim_to_budget("abcdefghijklmnopqrstuvwxyz", budget)
    assert len(result) <= 10
    assert result.endswith("...")


def test_context_assembler_keeps_layers_within_budget():
    assembler = ContextAssembler(ContextBudget(max_chars=40))
    bundle = assembler.assemble(
        [
            system_layer("system prompt"),
            agent_identity_layer("intel_officer", "agent profile"),
            recent_conversation_layer("x" * 80),
        ]
    )
    total_chars = sum(len(layer.content) for layer in bundle.layers)
    assert total_chars <= 40
    assert len(bundle.layers) >= 2


def test_context_assembler_to_text_renders_sections():
    assembler = ContextAssembler()
    bundle = assembler.assemble(
        [
            system_layer("system prompt"),
            project_memory_layer("default", "memory facts"),
        ]
    )
    rendered = assembler.to_text(bundle)
    assert "[system]" in rendered
    assert "[project_memory]" in rendered
    assert "memory facts" in rendered
