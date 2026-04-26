import pytest

from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.contracts.tool import ToolClass, ToolDescriptor
from quantamind_v2.core.runs.coordinator import RunCoordinator
from quantamind_v2.runtimes.tools import ToolIsolationMode, ToolIsolationResolver, ToolRuntimeExecutor
from quantamind_v2.runtimes.workers import InMemoryTaskWorker


def _sync_query_handler(value: str):
    return {"echo": value}


def _sync_delivery_handler(target: str):
    return {"sent_to": target}


def _sync_fail_handler():
    raise RuntimeError("tool boom")


async def _async_long_handler(value: int):
    return {"value": value * 2}


def test_tool_isolation_resolver_defaults():
    resolver = ToolIsolationResolver()
    profile = resolver.resolve(ToolClass.DEVICE_COMMAND)
    assert profile.isolation_mode == ToolIsolationMode.SUBPROCESS
    assert profile.requires_approval is True


@pytest.mark.asyncio
async def test_tool_runtime_executes_query_in_thread_profile():
    executor = ToolRuntimeExecutor()
    descriptor = ToolDescriptor(name="system_status", description="status", tool_class=ToolClass.QUERY)
    result = await executor.execute(descriptor, _sync_query_handler, value="ok")
    assert result.tool_name == "system_status"
    assert result.isolation_mode == "thread"
    assert result.output["echo"] == "ok"


@pytest.mark.asyncio
async def test_tool_runtime_executes_async_long_running_handler():
    executor = ToolRuntimeExecutor()
    descriptor = ToolDescriptor(name="digest", description="digest", tool_class=ToolClass.LONG_RUNNING)
    result = await executor.execute(descriptor, _async_long_handler, value=21)
    assert result.isolation_mode == "worker"
    assert result.output["value"] == 42


@pytest.mark.asyncio
async def test_tool_runtime_marks_external_delivery_as_approval_required():
    executor = ToolRuntimeExecutor()
    descriptor = ToolDescriptor(name="feishu_send", description="send", tool_class=ToolClass.EXTERNAL_DELIVERY)
    result = await executor.execute(descriptor, _sync_delivery_handler, target="feishu")
    assert result.requires_approval is True
    assert result.output["sent_to"] == "feishu"


@pytest.mark.asyncio
async def test_tool_runtime_worker_mode_uses_task_worker_and_syncs_run():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="queued")
    worker = InMemoryTaskWorker(coordinator=coordinator)
    executor = ToolRuntimeExecutor(task_worker=worker)
    descriptor = ToolDescriptor(name="digest", description="digest", tool_class=ToolClass.LONG_RUNNING)

    result = await executor.execute(
        descriptor,
        _async_long_handler,
        run_id=run.run_id,
        budget_seconds=2.0,
        value=21,
    )

    assert result.isolation_mode == "worker"
    assert result.task_id is not None
    assert result.task_state == "completed"
    assert result.output["value"] == 42
    synced = coordinator.get_run(run.run_id)
    assert synced.state == RunState.COMPLETED
    assert synced.stage == "worker_completed"


@pytest.mark.asyncio
async def test_tool_runtime_worker_mode_supports_background_submission():
    worker = InMemoryTaskWorker()
    executor = ToolRuntimeExecutor(task_worker=worker)
    descriptor = ToolDescriptor(name="digest", description="digest", tool_class=ToolClass.LONG_RUNNING)

    result = await executor.execute(
        descriptor,
        _async_long_handler,
        background=True,
        value=9,
    )

    assert result.task_id is not None
    assert result.task_state in {"queued", "running", "completed"}
    assert result.output["task_id"] == result.task_id


@pytest.mark.asyncio
async def test_tool_runtime_emits_standardized_tool_events():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="queued")
    executor = ToolRuntimeExecutor(coordinator=coordinator)
    descriptor = ToolDescriptor(name="system_status", description="status", tool_class=ToolClass.QUERY)

    result = await executor.execute(descriptor, _sync_query_handler, run_id=run.run_id, value="ok")

    assert result.output["echo"] == "ok"
    events = coordinator.list_events(run.run_id)
    event_types = [event.event_type for event in events]
    assert "tool_started" in event_types
    assert "tool_completed" in event_types


@pytest.mark.asyncio
async def test_tool_runtime_emits_tool_failed_event():
    coordinator = RunCoordinator()
    run = coordinator.create_run(RunType.SYSTEM, status_message="queued")
    executor = ToolRuntimeExecutor(coordinator=coordinator)
    descriptor = ToolDescriptor(name="system_status", description="status", tool_class=ToolClass.QUERY)

    with pytest.raises(RuntimeError):
        await executor.execute(descriptor, _sync_fail_handler, run_id=run.run_id)

    events = coordinator.list_events(run.run_id)
    event_types = [event.event_type for event in events]
    assert "tool_started" in event_types
    assert "tool_failed" in event_types
