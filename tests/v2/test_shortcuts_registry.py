from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _noop_handler():
    return {"ok": True}


def test_shortcut_registry_register_and_get():
    registry = ShortcutRegistry()
    definition = ShortcutDefinition(
        name="system_status",
        description="Check system status",
        handler=_noop_handler,
        triggers=["状态", "system status"],
    )
    registry.register(definition)
    assert registry.get("system_status") is definition


def test_shortcut_registry_match_on_trigger():
    registry = ShortcutRegistry()
    definition = ShortcutDefinition(
        name="intel_today",
        description="Send today's digest",
        handler=_noop_handler,
        triggers=["今天情报", "今日日报"],
    )
    registry.register(definition)
    assert registry.match("请发送今天情报") is definition
