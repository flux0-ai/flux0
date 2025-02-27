from abc import ABC, abstractmethod
from typing import Optional

from flux0_core.sessions import EventId
from flux0_stream.types import ChunkEvent, EmittedEvent


class EventStore(ABC):
    """ABC for event storage and retrieval."""

    @abstractmethod
    async def add_chunk(self, chunk: ChunkEvent) -> None: ...

    @abstractmethod
    async def finalize_event(
        self, correlation_id: str, event_id: EventId
    ) -> Optional[EmittedEvent]: ...
