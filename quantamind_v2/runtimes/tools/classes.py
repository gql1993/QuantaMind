from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantamind_v2.contracts.tool import ToolClass


class ToolIsolationMode(str, Enum):
    INLINE = "inline"
    THREAD = "thread"
    SUBPROCESS = "subprocess"
    WORKER = "worker"


@dataclass(slots=True)
class ToolExecutionProfile:
    tool_class: ToolClass
    isolation_mode: ToolIsolationMode
    requires_approval: bool = False


DEFAULT_TOOL_PROFILES = {
    ToolClass.QUERY: ToolExecutionProfile(
        tool_class=ToolClass.QUERY,
        isolation_mode=ToolIsolationMode.THREAD,
        requires_approval=False,
    ),
    ToolClass.MUTATION: ToolExecutionProfile(
        tool_class=ToolClass.MUTATION,
        isolation_mode=ToolIsolationMode.THREAD,
        requires_approval=False,
    ),
    ToolClass.LONG_RUNNING: ToolExecutionProfile(
        tool_class=ToolClass.LONG_RUNNING,
        isolation_mode=ToolIsolationMode.WORKER,
        requires_approval=False,
    ),
    ToolClass.EXTERNAL_DELIVERY: ToolExecutionProfile(
        tool_class=ToolClass.EXTERNAL_DELIVERY,
        isolation_mode=ToolIsolationMode.WORKER,
        requires_approval=True,
    ),
    ToolClass.DEVICE_COMMAND: ToolExecutionProfile(
        tool_class=ToolClass.DEVICE_COMMAND,
        isolation_mode=ToolIsolationMode.SUBPROCESS,
        requires_approval=True,
    ),
}
