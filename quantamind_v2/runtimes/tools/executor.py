from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from quantamind_v2.contracts.tool import ToolDescriptor
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.runtimes.tools.classes import ToolExecutionProfile, ToolIsolationMode
from quantamind_v2.runtimes.tools.isolation import ToolIsolationResolver
from quantamind_v2.runtimes.workers import InMemoryTaskWorker, TaskState


ToolHandler = Callable[..., Any]


@dataclass(slots=True)
class ToolExecutionResult:
    tool_name: str
    isolation_mode: str
    requires_approval: bool
    output: Any
    task_id: str | None = None
    task_state: str | None = None


class ToolRuntimeExecutor:
    """Phase 1 minimal tool runtime executor."""

    def __init__(
        self,
        resolver: ToolIsolationResolver | None = None,
        task_worker: InMemoryTaskWorker | None = None,
        coordinator: RunCoordinator | None = None,
    ) -> None:
        self.resolver = resolver or ToolIsolationResolver()
        self.task_worker = task_worker
        self.coordinator = coordinator

    async def execute(
        self,
        descriptor: ToolDescriptor,
        handler: ToolHandler,
        *,
        run_id: str | None = None,
        budget_seconds: float | None = None,
        max_retries: int = 0,
        background: bool = False,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        profile = self.resolver.resolve(descriptor.tool_class)
        self._emit_tool_event(
            run_id,
            "tool_started",
            {
                "tool_name": descriptor.name,
                "tool_class": descriptor.tool_class.value,
                "isolation_mode": profile.isolation_mode.value,
            },
        )
        task_id: str | None = None
        task_state: str | None = None
        try:
            if profile.isolation_mode == ToolIsolationMode.WORKER and self.task_worker is not None:
                task = self.task_worker.submit(
                    descriptor.name,
                    handler,
                    run_id=run_id,
                    budget_seconds=budget_seconds,
                    max_retries=max_retries,
                    **kwargs,
                )
                task_id = task.task_id
                if background:
                    output = {"task_id": task.task_id}
                    task_state = task.state.value
                else:
                    done = await self.task_worker.wait(task.task_id)
                    task_state = done.state.value
                    output = done.result if done.state == TaskState.COMPLETED else {"error": done.error}
            else:
                output = await self._execute_with_profile(profile, handler, **kwargs)
            result = ToolExecutionResult(
                tool_name=descriptor.name,
                isolation_mode=profile.isolation_mode.value,
                requires_approval=profile.requires_approval,
                output=output,
                task_id=task_id,
                task_state=task_state,
            )
            if task_state in {TaskState.FAILED.value, TaskState.CANCELLED.value, TaskState.TIMEOUT.value}:
                error_message = output.get("error") if isinstance(output, dict) else None
                self._emit_tool_event(
                    run_id,
                    "tool_failed",
                    {
                        "tool_name": descriptor.name,
                        "task_id": task_id,
                        "task_state": task_state,
                        "error": error_message,
                    },
                )
            else:
                self._emit_tool_event(
                    run_id,
                    "tool_completed",
                    {
                        "tool_name": descriptor.name,
                        "task_id": task_id,
                        "task_state": task_state,
                    },
                )
            return result
        except Exception as exc:
            self._emit_tool_event(
                run_id,
                "tool_failed",
                {
                    "tool_name": descriptor.name,
                    "task_id": task_id,
                    "task_state": task_state,
                    "error": str(exc),
                },
            )
            raise

    async def _execute_with_profile(
        self,
        profile: ToolExecutionProfile,
        handler: ToolHandler,
        **kwargs: Any,
    ) -> Any:
        if asyncio.iscoroutinefunction(handler):
            return await handler(**kwargs)

        if profile.isolation_mode in {ToolIsolationMode.THREAD, ToolIsolationMode.WORKER}:
            return await asyncio.to_thread(handler, **kwargs)

        if profile.isolation_mode in {ToolIsolationMode.INLINE, ToolIsolationMode.SUBPROCESS}:
            # Phase 1: subprocess is expressed as a policy choice, but still runs inline.
            return handler(**kwargs)

        raise ValueError(f"unsupported isolation mode: {profile.isolation_mode}")

    def _emit_tool_event(self, run_id: str | None, event_type: str, payload: dict[str, Any]) -> None:
        if not run_id or self.coordinator is None:
            return
        try:
            self.coordinator.append_event(run_id, event_type, payload)
        except KeyError:
            return
