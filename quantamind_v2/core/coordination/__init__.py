"""Multi-agent coordination skeleton for QuantaMind 2.0."""

from .router import CoordinationMode, CoordinationRouter
from .audit import CoordinationAuditEvent, CoordinationAuditStore
from .planner import CoordinationPlanner
from .persistence import (
    DualWriteCoordinationAuditStore,
    DualWriteCoordinationPolicyStore,
    FileBackedCoordinationAuditStore,
    FileBackedCoordinationPolicyStore,
    SQLiteCoordinationAuditStore,
    SQLiteCoordinationPolicyStore,
)
from .merger import CoordinationMerger
from .topology import CoordinationNode, CoordinationTopology
from .delegation import CoordinationDelegator
from .policies import CoordinationPolicies
from .scheduling import (
    CoordinationConflictDecision,
    CoordinationConflictStrategy,
    decide_coordination_conflict,
    detect_active_coordination_conflict,
)
from .supervisor import CoordinationSupervisor

__all__ = [
    "CoordinationDelegator",
    "CoordinationAuditEvent",
    "CoordinationAuditStore",
    "CoordinationConflictDecision",
    "CoordinationConflictStrategy",
    "CoordinationMerger",
    "CoordinationMode",
    "CoordinationNode",
    "CoordinationPlanner",
    "CoordinationPolicies",
    "CoordinationRouter",
    "CoordinationSupervisor",
    "CoordinationTopology",
    "DualWriteCoordinationAuditStore",
    "DualWriteCoordinationPolicyStore",
    "FileBackedCoordinationAuditStore",
    "FileBackedCoordinationPolicyStore",
    "SQLiteCoordinationAuditStore",
    "SQLiteCoordinationPolicyStore",
    "decide_coordination_conflict",
    "detect_active_coordination_conflict",
]
