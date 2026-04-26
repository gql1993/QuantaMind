from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CoordinationPolicySettings:
    default_conflict_strategy: str = "degrade_single_agent"
    audit_export_limit_max: int = 1000
    audit_retention_max_events: int = 2000
    audit_rotate_max_bytes: int = 1_000_000
    audit_rotate_interval_seconds: int = 86_400
    dual_write_enabled: bool = False
    database_read_preferred: bool = False
    database_read_fallback_to_file: bool = True
    database_read_profile_allowlist: list[str] | None = None
    database_read_rollout_percentage: int = 0
    database_path: str = ".quantamind_v2_runtime/coordination/coordination.db"
    state_dir: str = ".quantamind_v2_runtime/coordination"

    def to_dict(self) -> dict:
        return {
            "default_conflict_strategy": self.default_conflict_strategy,
            "audit_export_limit_max": self.audit_export_limit_max,
            "audit_retention_max_events": self.audit_retention_max_events,
            "audit_rotate_max_bytes": self.audit_rotate_max_bytes,
            "audit_rotate_interval_seconds": self.audit_rotate_interval_seconds,
            "dual_write_enabled": self.dual_write_enabled,
            "database_read_preferred": self.database_read_preferred,
            "database_read_fallback_to_file": self.database_read_fallback_to_file,
            "database_read_profile_allowlist": list(self.database_read_profile_allowlist or []),
            "database_read_rollout_percentage": self.database_read_rollout_percentage,
            "database_path": self.database_path,
            "state_dir": self.state_dir,
        }
