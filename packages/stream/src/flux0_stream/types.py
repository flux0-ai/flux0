import time
from abc import ABC
from dataclasses import dataclass, field
from typing import Literal, Mapping, Optional, TypedDict, Union

from flux0_core.sessions import (
    EventId,
    EventSource,
    EventType,
    MessageEventData,
    StatusEventData,
    ToolEventData,
)
from flux0_core.types import JSONSerializable


@dataclass(frozen=True)
class EmittedEvent:
    """Represents an event emitted by a source.
    This is the final form of an event after all chunks have been processed and
    closely related to the `Event` class in core.

    Attributes:
        source (EventSource): The source of the event.
        type (EventType): The type of the event.
        correlation_id (str): Unique identifier for the event stream.
        data (Union[MessageEventData, StatusEventData, ToolEventData]): The event data.
        metadata (Optional[Mapping[str, JSONSerializable]]): Additional metadata.
    """

    id: EventId
    source: EventSource
    type: EventType
    correlation_id: str
    data: Union[MessageEventData, StatusEventData, ToolEventData]
    metadata: Optional[Mapping[str, JSONSerializable]] = None


class AddOperation(TypedDict):
    op: Literal["add"]
    path: str
    value: JSONSerializable


class ReplaceOperation(TypedDict):
    op: Literal["replace"]
    path: str
    value: JSONSerializable


# Define a union of valid operations
JsonPatchOperation = Union[ReplaceOperation, AddOperation]


@dataclass(frozen=True)
class ChunkEvent(ABC):
    """Represents an incremental update using JSON Patch operations.

    Attributes:
        correlation_id (str): Unique identifier for the event stream.
        event_id (str): Unique identifier for the event.
        chunk_id (int): The sequence number of the chunk.
        content (str): The actual content of this chunk.
        timestamp (float): Time at which the chunk was received.
    """

    correlation_id: str
    event_id: EventId
    seq: int
    patches: list[JsonPatchOperation]
    metadata: Mapping[str, JSONSerializable] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
