from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from quantamind_v2.contracts.run import RunState
from quantamind_v2.core.runs.coordinator import RunCoordinator

TaskHandler = Callable[..., Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    task_name: str
    run_id: Optional[str] = None
    state: TaskState = TaskState.QUEUED
    attempt: int = 1
    max_retries: int = 0
    budget_seconds: Optional[float] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: str = ""
    parent_task_id: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "run_id": self.run_id,
            "state": self.state.value,
            "attempt": self.attempt,
            "max_retries": self.max_retries,
            "budget_seconds": self.budget_seconds,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "parent_task_id": self.parent_task_id,
        }


@dataclass(slots=True)
class _TaskRuntimeSpec:
    handler: TaskHandler
    kwargs: Dict[str, Any]


class InMemoryTaskWorker:
    """Phase 3 minimal in-memory worker with cancel/retry/budget."""

    def __init__(self, coordinator: RunCoordinator | None = None) -> None:
        self.coordinator = coordinator
        self._records: Dict[str, TaskRecord] = {}
        self._specs: Dict[str, _TaskRuntimeSpec] = {}
        self._futures: Dict[str, asyncio.Task] = {}

    def submit(
        self,
        task_name: str,
        handler: TaskHandler,
        *,
        run_id: str | None = None,
        budget_seconds: float | None = None,
        max_retries: int = 0,
        parent_task_id: str | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> TaskRecord:
        task_id = f"task-{uuid4().hex[:12]}"
        record = TaskRecord(
            task_id=task_id,
            task_name=task_name,
            run_id=run_id,
            budget_seconds=budget_seconds,
            max_retries=max(0, max_retries),
            attempt=attempt,
            parent_task_id=parent_task_id,
        )
        self._records[task_id] = record
        self._specs[task_id] = _TaskRuntimeSpec(handler=handler, kwargs=dict(kwargs))
        self._futures[task_id] = asyncio.create_task(self._execute(task_id))
        return record

    def get(self, task_id: str) -> TaskRecord:
        record = self._records.get(task_id)
        if record is None:
            raise KeyError(f"task not found: {task_id}")
        return record

    def list(self) -> list[TaskRecord]:
        return list(self._records.values())

    async def wait(self, task_id: str, timeout: float | None = None) -> TaskRecord:
        future = self._futures.get(task_id)
        if future is None:
            raise KeyError(f"task not found: {task_id}")
        try:
            await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
        except asyncio.CancelledError:
            pass
        return self.get(task_id)

    def cancel(self, task_id: str) -> TaskRecord:
        record = self.get(task_id)
        future = self._futures.get(task_id)
        if record.state in {TaskState.QUEUED, TaskState.RUNNING}:
            record.state = TaskState.CANCELLED
            record.error = "Task cancelled"
            now = utc_now_iso()
            record.updated_at = now
            record.completed_at = now
            self._sync_run_cancel(record)
        if future and not future.done():
            future.cancel()
        return record

    def retry(self, task_id: str) -> TaskRecord:
        prev = self.get(task_id)
        if prev.state not in {TaskState.FAILED, TaskState.TIMEOUT, TaskState.CANCELLED}:
            raise ValueError(f"task is not retryable: {prev.state.value}")
        if prev.attempt > prev.max_retries:
            raise ValueError(f"retry limit reached: attempt={prev.attempt}, max_retries={prev.max_retries}")
        spec = self._specs.get(task_id)
        if spec is None:
            raise KeyError(f"task spec not found: {task_id}")
        return self.submit(
            prev.task_name,
            spec.handler,
            run_id=prev.run_id,
            budget_seconds=prev.budget_seconds,
            max_retries=prev.max_retries,
            parent_task_id=prev.task_id,
            attempt=prev.attempt + 1,
            **spec.kwargs,
        )

    async def _execute(self, task_id: str) -> None:
        record = self.get(task_id)
        spec = self._specs[task_id]
        record.state = TaskState.RUNNING
        record.started_at = utc_now_iso()
        record.updated_at = record.started_at
        self._sync_run_state(record, entering=True)
        try:
            if record.budget_seconds and record.budget_seconds > 0:
                result = await asyncio.wait_for(
                    self._invoke_handler(spec.handler, spec.kwargs),
                    timeout=record.budget_seconds,
                )
            else:
                result = await self._invoke_handler(spec.handler, spec.kwargs)
            record.result = result
            record.state = TaskState.COMPLETED
            record.error = ""
            self._sync_run_success(record)
        except asyncio.TimeoutError:
            record.state = TaskState.TIMEOUT
            record.error = f"Task exceeded budget ({record.budget_seconds}s)"
            self._sync_run_failure(record, reason=record.error)
        except asyncio.CancelledError:
            record.state = TaskState.CANCELLED
            record.error = "Task cancelled"
            self._sync_run_cancel(record)
            raise
        except Exception as exc:  # noqa: BLE001
            record.state = TaskState.FAILED
            record.error = str(exc)
            self._sync_run_failure(record, reason=record.error)
        finally:
            record.completed_at = utc_now_iso()
            record.updated_at = record.completed_at

    async def _invoke_handler(self, handler: TaskHandler, kwargs: Dict[str, Any]) -> Any:
        if asyncio.iscoroutinefunction(handler):
            return await handler(**kwargs)
        value = await asyncio.to_thread(handler, **kwargs)
        if inspect.isawaitable(value):
            return await value
        return value

    def _sync_run_state(self, record: TaskRecord, *, entering: bool = False) -> None:
        if self.coordinator is None or record.run_id is None:
            return
        try:
            run = self.coordinator.get_run(record.run_id)
        except KeyError:
            return
        message = f"Worker task `{record.task_name}` started (attempt {record.attempt})."
        if entering and run.state == RunState.QUEUED:
            self.coordinator.transition(
                run.run_id,
                RunState.RUNNING,
                stage="worker_running",
                status_message=message,
            )
            return
        self.coordinator.update_run(run.run_id, stage="worker_running", status_message=message)

    def _sync_run_success(self, record: TaskRecord) -> None:
        if self.coordinator is None or record.run_id is None:
            return
        try:
            run = self.coordinator.get_run(record.run_id)
        except KeyError:
            return
        status_message = f"Worker task `{record.task_name}` completed."
        self.coordinator.update_run(
            run.run_id,
            stage="worker_completed",
            status_message=status_message,
            metadata={"worker_task_id": record.task_id},
        )
        if run.state == RunState.RUNNING:
            self.coordinator.transition(
                run.run_id,
                RunState.COMPLETED,
                stage="worker_completed",
                status_message=status_message,
            )

    def _sync_run_failure(self, record: TaskRecord, *, reason: str) -> None:
        if self.coordinator is None or record.run_id is None:
            return
        try:
            run = self.coordinator.get_run(record.run_id)
        except KeyError:
            return
        status_message = f"Worker task `{record.task_name}` failed: {reason}"
        self.coordinator.update_run(
            run.run_id,
            stage="worker_failed",
            status_message=status_message,
            metadata={"worker_task_id": record.task_id, "worker_error": reason},
        )
        if run.state == RunState.RUNNING:
            self.coordinator.transition(
                run.run_id,
                RunState.FAILED,
                stage="worker_failed",
                status_message=status_message,
            )

    def _sync_run_cancel(self, record: TaskRecord) -> None:
        if self.coordinator is None or record.run_id is None:
            return
        try:
            run = self.coordinator.get_run(record.run_id)
        except KeyError:
            return
        status_message = f"Worker task `{record.task_name}` cancelled."
        self.coordinator.update_run(
            run.run_id,
            stage="worker_cancelled",
            status_message=status_message,
            metadata={"worker_task_id": record.task_id},
        )
        if run.state == RunState.RUNNING:
            self.coordinator.transition(
                run.run_id,
                RunState.CANCELLED,
                stage="worker_cancelled",
                status_message=status_message,
            )
