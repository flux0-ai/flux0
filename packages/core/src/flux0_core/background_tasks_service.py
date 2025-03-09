# Define a type alias for background tasks that do not return a value.
import asyncio
import traceback
from typing import Any, Coroutine, Dict, Optional, Self, TypeAlias

from flux0_core.logging import Logger

# Define a type alias for background tasks that do not return a value.
Task: TypeAlias = asyncio.Task[None]


class BackgroundTaskService:
    """A service for managing background tasks."""

    def __init__(self, logger: Logger) -> None:
        self._logger: Logger = logger
        self._last_garbage_collection: float = 0.0
        self._garbage_collection_interval: float = 5.0
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> Self:
        self._collector_task = asyncio.create_task(self._run_collector())
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        tb: Optional[Any],
    ) -> bool:
        # Only cancel tasks if exiting due to an exception (shutdown).
        if exc_value:
            await self.cancel_all(reason="Shutting down due to exception")
        self._logger.info(f"{type(self).__name__}: Exiting context, cleaning up tasks")
        await self.collect(force=True)
        return False

    async def cancel(self, *, tag: str, reason: str = "(not set)") -> None:
        """
        Cancels the task identified by the given tag.
        """
        async with self._lock:
            task = self._tasks.get(tag)
            if task and not task.done():
                task.cancel(f"Forced cancellation by {type(self).__name__} [reason: {reason}]")
                self._logger.info(f"{type(self).__name__}: Cancelled task '{tag}'")
        await self.collect()

    async def cancel_all(self, *, reason: str = "(not set)") -> None:
        """
        Cancels all running tasks.
        """
        async with self._lock:
            self._logger.info(
                f"{type(self).__name__}: Cancelling all remaining tasks ({len(self._tasks)}) [reason: {reason}]"
            )
            for tag, task in self._tasks.items():
                if not task.done():
                    task.cancel(f"Forced cancellation by {type(self).__name__} [reason: {reason}]")
        await self.collect()

    async def start(self, coro: Coroutine[Any, Any, None], /, *, tag: str) -> Task:
        """
        Starts a new background task using the provided coroutine and associates it with the given tag.
        Raises an exception if a task with the same tag is already running.
        """
        await self.collect()
        async with self._lock:
            if tag in self._tasks and not self._tasks[tag].done():
                raise Exception(
                    f"Task '{tag}' is already running; consider calling restart() instead"
                )
            self._logger.info(f"{type(self).__name__}: Starting task '{tag}'")
            task: Task = asyncio.create_task(coro)
            self._tasks[tag] = task
            return task

    async def restart(self, coro: Coroutine[Any, Any, None], /, *, tag: str) -> Task:
        """
        Restarts the background task identified by the given tag.
        If an existing task is running, it will be canceled and awaited before starting a new one.
        """
        await self.collect()
        async with self._lock:
            if tag in self._tasks:
                existing_task = self._tasks[tag]
                if not existing_task.done():
                    existing_task.cancel(f"Restarting task '{tag}'")
                    await self._await_task(existing_task)
            self._logger.info(f"{type(self).__name__}: Restarting task '{tag}'")
            task: Task = asyncio.create_task(coro)
            self._tasks[tag] = task
            return task

    async def collect(self, *, force: bool = False) -> None:
        """
        Cleans up finished tasks from the internal registry.
        If 'force' is True, it waits for all tasks to finish before cleanup.
        """
        now: float = asyncio.get_running_loop().time()
        if not force and (now - self._last_garbage_collection) < self._garbage_collection_interval:
            return

        async with self._lock:
            new_tasks: Dict[str, Task] = {}
            for tag, task in self._tasks.items():
                if task.done() or force:
                    if not task.done():
                        self._logger.info(
                            f"{type(self).__name__}: Waiting for task '{tag}' to finish before cleanup"
                        )
                    await self._await_task(task)
                else:
                    new_tasks[tag] = task
            self._tasks = new_tasks
        self._last_garbage_collection = now

    async def _await_task(self, task: Task) -> None:
        """
        Awaits the task and logs exceptions if they occur.
        """
        try:
            await task
        except asyncio.CancelledError:
            pass  # Task was cancelled, no further action needed.
        except Exception as exc:
            self._logger.warning(
                f"{type(self).__name__}: Task raised an exception: {''.join(traceback.format_exception_only(type(exc), exc)).strip()}"
            )

    async def _run_collector(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._garbage_collection_interval)
                await self.collect()
        except asyncio.CancelledError:
            pass
