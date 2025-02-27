# Type aliases for event subscribers
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional

from flux0_core.sessions import EventId, StatusEventData
from flux0_stream.types import ChunkEvent, EmittedEvent

ProcessedSubscriber = Callable[[ChunkEvent], Awaitable[None]]
FinalSubscriber = Callable[[EmittedEvent], Awaitable[None]]


class EventEmitter(ABC):
    """ABC for event emissions."""

    @abstractmethod
    async def enqueue_status_event(
        self,
        correlation_id: str,
        data: StatusEventData,
        event_id: Optional[EventId] = None,
    ) -> None:
        """Enqueues a status event for a specific execution (correlation_id)."""
        ...

    @abstractmethod
    async def enqueue_event_chunk(self, chunk: ChunkEvent) -> None:
        """Accepts an implementation of event chunk and processes it."""
        ...

    @abstractmethod
    def subscribe_processed(self, correlation_id: str, subscriber: ProcessedSubscriber) -> None:
        """Registers a subscriber to receive event chunks for a specific execution (correlation_id)."""
        ...

    @abstractmethod
    def subscribe_final(self, correlation_id: str, subscriber: FinalSubscriber) -> None:
        """Registers a subscriber to receive finalized events for a specific execution (correlation_id)."""
        ...

    @abstractmethod
    def unsubscribe_processed(self, correlation_id: str, subscriber: ProcessedSubscriber) -> None:
        """Removes a processed chunk subscriber for a specific execution (correlation_id)."""
        ...

    @abstractmethod
    def unsubscribe_final(self, correlation_id: str, subscriber: FinalSubscriber) -> None:
        """Removes a finalized event subscriber for a specific execution (correlation_id)."""
        ...
