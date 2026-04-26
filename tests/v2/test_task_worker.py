import asyncio

import pytest

from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.runtimes.workers import InMemoryTaskWorker, TaskState


def _ok_handler(value: int):
    return {"value": value * 2}


async def _slow_handler(delay: float = 0.2):
    await asyncio.sleep(delay)
    return {"status": "ok"}


def _fail_handler():
    raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_task_worker_completes_and_updates_run():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="queued")
    worker = InMemoryTaskWorker(coordinator=coordinator)

    task = worker.submit("system_status_refresh", _ok_handler, run_id=run.run_id, value=21)
    done = await worker.wait(task.task_id, timeout=2.0)

    assert done.state == TaskState.COMPLETED
    assert done.result["value"] == 42
    synced_run = coordinator.get_run(run.run_id)
    assert synced_run.state == RunState.COMPLETED
    assert synced_run.stage == "worker_completed"
    assert synced_run.metadata.get("worker_task_id") == task.task_id


@pytest.mark.asyncio
async def test_task_worker_marks_timeout():
    worker = InMemoryTaskWorker()
    task = worker.submit("slow_task", _slow_handler, delay=0.1, budget_seconds=0.01)
    done = await worker.wait(task.task_id, timeout=1.0)

    assert done.state == TaskState.TIMEOUT
    assert "budget" in done.error


@pytest.mark.asyncio
async def test_task_worker_can_cancel():
    worker = InMemoryTaskWorker()
    task = worker.submit("cancel_task", _slow_handler, delay=0.4)
    worker.cancel(task.task_id)
    done = await worker.wait(task.task_id, timeout=1.0)

    assert done.state == TaskState.CANCELLED
    assert done.error == "Task cancelled"


@pytest.mark.asyncio
async def test_task_worker_retry_after_failure():
    worker = InMemoryTaskWorker()
    failed = worker.submit("retry_task", _fail_handler, max_retries=1)
    done = await worker.wait(failed.task_id, timeout=1.0)
    assert done.state == TaskState.FAILED

    retry_task = worker.retry(failed.task_id)
    retried = await worker.wait(retry_task.task_id, timeout=1.0)
    assert retried.attempt == 2
    assert retried.parent_task_id == failed.task_id
    assert retried.state == TaskState.FAILED

    with pytest.raises(ValueError):
        worker.retry(retry_task.task_id)
