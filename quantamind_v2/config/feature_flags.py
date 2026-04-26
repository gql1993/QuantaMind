from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeatureFlags:
    enable_models_runtime: bool = True
    enable_mcp_runtime: bool = True
    enable_memory_bridge: bool = True
    enable_planning_preview: bool = True
    enable_integrations_api: bool = True

    def to_dict(self) -> dict:
        return {
            "enable_models_runtime": self.enable_models_runtime,
            "enable_mcp_runtime": self.enable_mcp_runtime,
            "enable_memory_bridge": self.enable_memory_bridge,
            "enable_planning_preview": self.enable_planning_preview,
            "enable_integrations_api": self.enable_integrations_api,
        }
