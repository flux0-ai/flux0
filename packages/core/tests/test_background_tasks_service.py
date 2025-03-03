# A simple coroutine that waits for a given delay and then appends its tag to a shared list.
import asyncio
from typing import List

from flux0_core.background_tasks_service import BackgroundTaskService
from flux0_core.logging import Logger


async def dummy_task(delay: float, results: List[str], tag: str) -> None:
    await asyncio.sleep(delay)
    results.append(tag)


# A coroutine that never finishes (unless cancelled)
async def never_ending_task() -> None:
    await asyncio.Event().wait()


async def test_start_task(logger: Logger) -> None:
    results: List[str] = []
    async with BackgroundTaskService(logger) as service:
        # Start a task that completes quickly.
        await service.start(dummy_task(0.1, results, "test1"), tag="test1")
        await asyncio.sleep(0.2)  # Wait for task to complete.
        # Force cleanup.
        await service.collect(force=True)
        # The task should have run to completion and appended its tag.
        assert "test1" in results
        # The tasks dictionary should be empty after cleanup.
        assert len(service._tasks) == 0


async def test_cancel_task(logger: Logger) -> None:
    results: List[str] = []
    async with BackgroundTaskService(logger) as service:
        # Start a task that takes longer to complete.
        await service.start(dummy_task(1, results, "test_cancel"), tag="test_cancel")
        # Cancel the task before it completes.
        await service.cancel(tag="test_cancel", reason="unit test cancellation")
        await asyncio.sleep(0.1)  # Give some time for cancellation to propagate.
        await service.collect(force=True)
        # The task should not have appended its tag since it was cancelled.
        assert "test_cancel" not in results
        assert len(service._tasks) == 0


async def test_restart_task(logger: Logger) -> None:
    results: List[str] = []
    async with BackgroundTaskService(logger) as service:
        # Start a long-running task.
        await service.start(dummy_task(1, results, "initial"), tag="test_restart")
        # Restart it with a new coroutine that finishes quickly.
        await service.restart(dummy_task(0.1, results, "restarted"), tag="test_restart")
        await asyncio.sleep(0.2)  # Wait for restarted task to finish.
        await service.collect(force=True)
        # Only the restarted task should have completed.
        assert "restarted" in results
        assert "initial" not in results
        assert len(service._tasks) == 0


async def test_aexit_with_exception_cancels_tasks(logger: Logger) -> None:
    # Instantiate the service without using the async context manager
    # so that we can simulate an exception on exit.
    service = BackgroundTaskService(logger)
    try:
        await service.__aenter__()
        # Start a never-ending task.
        await service.start(never_ending_task(), tag="shutdown_test")
        # Simulate an exception that triggers shutdown.
        raise RuntimeError("Test exception")
    except RuntimeError:
        # On exception, __aexit__ should cancel tasks.
        await service.__aexit__(RuntimeError, RuntimeError("Test exception"), None)
        await service.collect(force=True)
        # The task should be cancelled and removed.
        assert "shutdown_test" not in service._tasks
