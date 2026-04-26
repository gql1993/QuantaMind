from __future__ import annotations

from dataclasses import dataclass, field

from quantamind_v2.config.coordination import CoordinationPolicySettings
from quantamind_v2.config.feature_flags import FeatureFlags
from quantamind_v2.config.providers import ProviderSettings
from quantamind_v2.config.runtime_limits import RuntimeLimits


@dataclass(slots=True)
class AppSettings:
    app_name: str = "QuantaMind Gateway V2"
    app_version: str = "0.2.0-dev"
    feature_flags: FeatureFlags = field(default_factory=FeatureFlags)
    runtime_limits: RuntimeLimits = field(default_factory=RuntimeLimits)
    providers: ProviderSettings = field(default_factory=ProviderSettings)
    coordination: CoordinationPolicySettings = field(default_factory=CoordinationPolicySettings)

    def to_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "feature_flags": self.feature_flags.to_dict(),
            "runtime_limits": self.runtime_limits.to_dict(),
            "providers": self.providers.to_dict(),
            "coordination": self.coordination.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "AppSettings":
        feature_flags = payload.get("feature_flags") or {}
        runtime_limits = payload.get("runtime_limits") or {}
        providers = payload.get("providers") or {}
        coordination = payload.get("coordination") or {}
        return cls(
            app_name=str(payload.get("app_name", "QuantaMind Gateway V2")),
            app_version=str(payload.get("app_version", "0.2.0-dev")),
            feature_flags=FeatureFlags(
                enable_models_runtime=bool(feature_flags.get("enable_models_runtime", True)),
                enable_mcp_runtime=bool(feature_flags.get("enable_mcp_runtime", True)),
                enable_memory_bridge=bool(feature_flags.get("enable_memory_bridge", True)),
                enable_planning_preview=bool(feature_flags.get("enable_planning_preview", True)),
                enable_integrations_api=bool(feature_flags.get("enable_integrations_api", True)),
            ),
            runtime_limits=RuntimeLimits(
                default_task_timeout_seconds=float(runtime_limits.get("default_task_timeout_seconds", 20.0)),
                default_model_timeout_seconds=float(runtime_limits.get("default_model_timeout_seconds", 15.0)),
                default_mcp_timeout_seconds=float(runtime_limits.get("default_mcp_timeout_seconds", 10.0)),
                default_prompt_budget_chars=int(runtime_limits.get("default_prompt_budget_chars", 12000)),
            ),
            providers=ProviderSettings(
                model_default_provider=str(providers.get("model_default_provider", "mock_echo")),
                model_fallback_provider=str(providers.get("model_fallback_provider", "mock_echo")),
                model_default_name=str(providers.get("model_default_name", "mock-echo-v1")),
                gateway_base_url=str(providers.get("gateway_base_url", "http://127.0.0.1:18790")),
            ),
            coordination=CoordinationPolicySettings(
                default_conflict_strategy=str(
                    coordination.get("default_conflict_strategy", "degrade_single_agent")
                ),
                audit_export_limit_max=max(int(coordination.get("audit_export_limit_max", 1000)), 1),
                audit_retention_max_events=max(int(coordination.get("audit_retention_max_events", 2000)), 100),
                audit_rotate_max_bytes=max(int(coordination.get("audit_rotate_max_bytes", 1_000_000)), 1),
                audit_rotate_interval_seconds=max(int(coordination.get("audit_rotate_interval_seconds", 86_400)), 1),
                dual_write_enabled=bool(coordination.get("dual_write_enabled", False)),
                database_read_preferred=bool(coordination.get("database_read_preferred", False)),
                database_read_fallback_to_file=bool(coordination.get("database_read_fallback_to_file", True)),
                database_read_profile_allowlist=[
                    str(item).strip()
                    for item in list(coordination.get("database_read_profile_allowlist") or [])
                    if str(item).strip()
                ],
                database_read_rollout_percentage=min(
                    max(int(coordination.get("database_read_rollout_percentage", 0)), 0),
                    100,
                ),
                database_path=str(
                    coordination.get("database_path", ".quantamind_v2_runtime/coordination/coordination.db")
                ),
                state_dir=str(coordination.get("state_dir", ".quantamind_v2_runtime/coordination")),
            ),
        )
