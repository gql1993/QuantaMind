from __future__ import annotations

from typing import Any

from quantamind_v2.config.settings import AppSettings


def merge_settings_overrides(base: AppSettings, overrides: dict[str, Any] | None = None) -> AppSettings:
    if not overrides:
        return base
    payload = base.to_dict()
    _deep_update(payload, overrides)
    return AppSettings.from_dict(payload)


def _deep_update(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
