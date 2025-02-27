import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Self, Union

from flux0_core.agents import AgentId
from flux0_core.logging import Logger
from flux0_core.sessions import EventId, SessionId, StatusEventData
from flux0_stream.emitter.api import (
    EventEmitter,
    FinalSubscriber,
    ProcessedSubscriber,
)
from flux0_stream.store.api import EventStore
from flux0_stream.types import ChunkEvent, EmittedEvent


@dataclass
class QueueMessage:
    """Represents a message in the event queue, distinguishing between event chunks and status events."""

    correlation_id: str
    event_id: Optional[EventId]
    data: Union[ChunkEvent, StatusEventData]


class MemoryEventEmitter(EventEmitter):
    """
    In-memory implementation of EventEmitter using asyncio.Queue.

    - Uses a **single** `asyncio.Queue[QueueMessage]` for processing both event chunks and status updates.
    - Handles **event finalization** when receiving a status event with `"ready"` or `"completed"`.
    - Supports **subscriber notifications** for both **processed chunks** and **finalized events**.
    - Implements a **worker loop** that continuously processes queued messages.
    - Ensures **clean shutdown**, processing remaining messages before stopping.
    """

    def __init__(self, event_store: EventStore, logger: Logger) -> None:
        """Initializes the event emitter with an event queue and subscriber management."""
        self.event_store: EventStore = event_store
        self.logger: Logger = logger

        # Queue to process events asynchronously
        self.queue: asyncio.Queue[QueueMessage] = asyncio.Queue()

        # Subscriber storage
        self.processed_subscribers: Dict[str, List[ProcessedSubscriber]] = {}
        self.final_subscribers: Dict[str, List[FinalSubscriber]] = {}

        # Worker task
        self._worker_task: asyncio.Task[None] = asyncio.create_task(self._worker_loop())

    async def enqueue_status_event(
        self,
        correlation_id: str,
        data: StatusEventData,
        event_id: Optional[EventId] = None,
    ) -> None:
        """Enqueues a status event for a specific execution (correlation_id)."""
        await self.queue.put(QueueMessage(correlation_id, event_id, data))

    async def enqueue_event_chunk(self, chunk: ChunkEvent) -> None:
        """Enqueues an event chunk for processing."""
        await self.queue.put(QueueMessage(chunk.correlation_id, chunk.event_id, chunk))

    def subscribe_processed(self, correlation_id: str, subscriber: ProcessedSubscriber) -> None:
        """Registers a subscriber to receive event chunks for a specific execution (correlation_id)."""
        self.processed_subscribers.setdefault(correlation_id, []).append(subscriber)

    def subscribe_final(self, correlation_id: str, subscriber: FinalSubscriber) -> None:
        """Registers a subscriber to receive finalized events for a specific execution (correlation_id)."""
        self.final_subscribers.setdefault(correlation_id, []).append(subscriber)

    def unsubscribe_processed(self, correlation_id: str, subscriber: ProcessedSubscriber) -> None:
        """Removes a processed chunk subscriber for a specific execution (correlation_id)."""
        if correlation_id in self.processed_subscribers:
            self.processed_subscribers[correlation_id].remove(subscriber)

    def unsubscribe_final(self, correlation_id: str, subscriber: FinalSubscriber) -> None:
        """Removes a finalized event subscriber for a specific execution (correlation_id)."""
        if correlation_id in self.final_subscribers:
            self.final_subscribers[correlation_id].remove(subscriber)

    async def _worker_loop(self) -> None:
        """Background task that processes messages from the queue."""
        while True:
            message: Optional[QueueMessage] = None
            try:
                message = await self.queue.get()
                if isinstance(message.data, ChunkEvent):
                    await self._process_event_chunk(message.correlation_id, message.data)
                elif isinstance(message.data, dict) and "status" in message.data:
                    await self._process_status_event(
                        message.correlation_id, message.event_id, message.data
                    )
            except asyncio.CancelledError:
                break  # Exit cleanly on shutdown
            except Exception as e:
                self.logger.error(
                    f"Error processing message: {e}", exc_info=True
                )  # Log errors safely
            finally:
                if message is not None:
                    self.queue.task_done()  # Only call task_done if a message was actually retrieved

    async def _process_event_chunk(self, correlation_id: str, chunk: ChunkEvent) -> None:
        """Processes an event chunk and notifies processed subscribers."""

        # Ensure the patch is in `JsonPatch` format
        # patch_obj = JsonPatch(chunk.patches)

        # Add chunk to event store
        await self.event_store.add_chunk(chunk)

        # Notify processed subscribers
        if correlation_id in self.processed_subscribers:
            for subscriber in self.processed_subscribers[correlation_id]:
                await subscriber(chunk)

    async def _process_status_event(
        self, correlation_id: str, event_id: Optional[EventId], data: StatusEventData
    ) -> None:
        """Processes a status event, finalizing events if required."""
        is_final: bool = data["status"] in {"ready"}

        if is_final:
            if event_id is None:
                raise ValueError("Event ID is required for finalization")

            # Ensure all chunks are processed before finalizing
            finalized_event = await self.event_store.finalize_event(correlation_id, event_id)
            if finalized_event is None:
                raise ValueError(f"Failed to finalize event for event_id: {event_id}")

            # Notify final subscribers
            if correlation_id in self.final_subscribers:
                for subscriber in self.final_subscribers[correlation_id]:
                    await subscriber(finalized_event)
        else:
            # Notify final subscribers for non final status updates
            if correlation_id in self.final_subscribers:
                for subscriber in self.final_subscribers[correlation_id]:
                    await subscriber(
                        EmittedEvent(
                            id=event_id if event_id is not None else EventId(""),
                            correlation_id=correlation_id,
                            source="ai_agent",
                            type="status",
                            data=data,
                        )
                    )

    async def shutdown(self) -> None:
        """Shuts down the event emitter, ensuring all queued events are processed."""
        self.logger.debug("Shutting down EventEmitter, processing remaining messages...")

        # Cancel the worker task
        self._worker_task.cancel()
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass

        # Process remaining messages in queue
        try:
            while not self.queue.empty():
                self.logger.debug("Processing remaining messages...")
                message: QueueMessage = self.queue.get_nowait()
                if isinstance(message.data, ChunkEvent):
                    await self._process_event_chunk(message.correlation_id, message.data)
                elif isinstance(message.data, dict) and "status" in message.data:
                    await self._process_status_event(
                        message.correlation_id, message.event_id, message.data
                    )

                # Ensure task_done() is only called if the message was actually retrieved
                self.queue.task_done()
        except asyncio.QueueEmpty:
            pass  # Safe exit if the queue is empty
        except Exception as e:
            self.logger.error(f"Error processing remaining messages: {e}", exc_info=True)

        self.logger.debug("EventEmitter shutdown complete.")

    async def __aenter__(self) -> Self:
        """Allows the event emitter to be used with an async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[object],
    ) -> None:
        """Ensures the event emitter shuts down properly when used in an async context manager."""
        await self.shutdown()


class InMemoryEventEmitterFactory:
    # Retained for compatibility.
    def __init__(self, event_emitter: EventEmitter) -> None:
        self._event_emitter = event_emitter

    async def create_event_emitter(
        self,
        emitting_agent_id: AgentId,
        session_id: SessionId,
    ) -> EventEmitter:
        return self._event_emitter
