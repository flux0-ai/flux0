# ===========================
# Message event data
# ===========================

import time
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Literal, Mapping, Optional, Sequence, TypeAlias, Union

import dateutil.parser
from fastapi import Path, Query
from flux0_core.sessions import EventId, ToolCallPartType, ToolCallResultType
from pydantic import Field, RootModel

from flux0_api.common import (
    DEFAULT_MODEL_CONFIG,
    DefaultBaseEnum,
    DefaultBaseModel,
    ExampleJson,
    JSONSerializableDTO,
)
from flux0_api.types_agents import agent_id_example, agent_name_examples
from flux0_api.types_patch import JsonPatchOperationDTO

user_input_content_example = "What's the weather in SF?"

text_part_example: ExampleJson = {
    "type": "text",
    "text": user_input_content_example,
}


class ContentPartDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": text_part_example,
    }

    """
    Represents a content part of a message.
    """

    type: Literal["content"]
    content: JSONSerializableDTO


reason_part_example: ExampleJson = {
    "type": "reasoning",
    "reasoning": "The user has requested me to check the weather in SF, I should probably call the weather API for San Francisco.",
}


class ReasoningPartDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": reason_part_example,
    }

    """
    Represents a reasoning part of a message.
    """

    type: Literal["reasoning"]
    reasoning: JSONSerializableDTO


class ToolPartDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "type": str(ToolCallPartType),
            "tool_call_id": "call01",
            "tool_name": "search",
            "args": {"query": "San Francisco weather"},
        },
    }

    """
    Represents a tool call (request) part of a message.
    """

    type: ToolCallPartType
    tool_call_id: str  # Used to match the tool call with the tool result
    tool_name: str
    args: JSONSerializableDTO


participant_example: ExampleJson = {
    "id": "i5f9zYvtJ4",
    "display_name": "John Doe",
}


MessagePartsType = Annotated[
    Union[ContentPartDTO, ReasoningPartDTO, ToolPartDTO], Field(discriminator="type")
]


class MessageEventDataDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {"parts": [text_part_example], "participant": participant_example},
    }

    """
    Data payload for message events.
    """

    type: Literal["message"]
    tags: Optional[Sequence[str]] = None
    flagged: Optional[bool] = None
    parts: Sequence[MessagePartsType]
    participant: Optional[dict[str, str]] = None


# ===========================
# Status event data
# ===========================


class StatusEventDataStatusField(Enum):
    """
    Status of the event.
    """

    ACKNOWLEDGE = "acknowledged"
    CANCELLED = "cancelled"
    PROCESSING = "processing"
    READY = "ready"
    TYPING = "typing"
    ERROR = "error"
    COMPLETED = "completed"


class StatusEventDataDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "status": "error",
            "acknowledged_offset": 4,
            "data": {"exception": "Traceback (most recent call last):\n..."},
        },
    }

    """
    Data payload for status events.
    """
    type: Literal["status"]
    status: StatusEventDataStatusField
    acknowledged_offset: Optional[int] = None
    data: Optional[JSONSerializableDTO] = None


# ===========================
# Tool call event data
# ===========================


class ControlOptions(DefaultBaseModel):
    mode: Literal["auto", "manual"]


class ToolResultDTO(DefaultBaseModel):
    data: JSONSerializableDTO
    metadata: Mapping[str, JSONSerializableDTO]
    control: ControlOptions


tool_call_example: ExampleJson = {
    "tool_call_id": "call01",
    "tool_name": "search",
    "args": {"query": "San Francisco weather"},
    "result": "It's 60 degrees and foggy.",
    "error": None,
}


class ToolCallDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": tool_call_example,
    }

    """
    Represents a tool call.
    """

    tool_call_id: str
    tool_name: str
    args: Mapping[str, JSONSerializableDTO]
    result: Optional[ToolResultDTO] = None
    error: Optional[str] = None


class ToolEventDataDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {"tool_calls": [tool_call_example]},
    }

    """
    Data payload for tool events.
    """
    type: ToolCallResultType
    tool_calls: list[ToolCallDTO]


# ===========================
# Event props
# ===========================
class EventSourceDTO(DefaultBaseEnum):
    """
    Source of the event within a session.

    Identifies who or what generated the event.
    """

    USER = "user"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"


event_id_example = "o5kf8vKzI5"

EventIdPath: TypeAlias = Annotated[
    EventId,
    Path(
        description="Unique identifier for the event",
        examples=[event_id_example],
    ),
]

correlation_id_example = "RID(lyH-sVmwJO)::Y8oBzYT4CQ"
EventCorrelationIdField: TypeAlias = Annotated[
    str,
    Field(
        description="Identifier linking related events together",
        examples=[correlation_id_example],
    ),
]


class EventTypeDTO(DefaultBaseEnum):
    """
    Type of event that occurred within a session.

    Represents different types of interactions that can occur within a conversation.
    """

    MESSAGE = "message"
    TOOL = "tool"
    STATUS = "status"
    CUSTOM = "custom"


# ===========================
# Event
# ===========================
EventCreatedAtField: TypeAlias = Annotated[
    datetime,
    Field(
        description="When the event was created",
        examples=[dateutil.parser.parse("2025-01-29T09:27:41")],
    ),
]

EventOffsetField: TypeAlias = Annotated[
    int,
    Field(
        description="Sequential position of the event in the session",
        examples=[0, 1, 2],
        ge=0,
    ),
]

event_example: ExampleJson = {
    "id": event_id_example,
    "correlation_id": correlation_id_example,
    "source": "user",
    "type": "message",
    "offset": 0,
    "data": {
        "type": "message",
        "parts": [
            {
                "type": "content",
                "content": "The weather in San Francisco is currently 60 degrees and foggy.",
            }
        ],
        "participant": participant_example,
    },
    "metadata": {"agent_id": agent_id_example, "agent_name": agent_name_examples[0]},
    "created_at": "2025-01-29T09:27:41Z",
}


class EventDTO(
    DefaultBaseModel,
    json_schema_extra={"example": event_example},
):
    id: EventIdPath
    correlation_id: EventCorrelationIdField
    type: EventTypeDTO
    source: EventSourceDTO
    offset: EventOffsetField
    data: Annotated[
        Union[MessageEventDataDTO, StatusEventDataDTO, ToolEventDataDTO],
        Field(discriminator="type"),
    ]
    deleted: bool
    metadata: Optional[Mapping[str, JSONSerializableDTO]] = None
    created_at: EventCreatedAtField


class EventsDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "data": [event_example],
        }
    }

    """
    List of events that occurred within a session.
    """
    data: Sequence[EventDTO]


# ===========================
# ChunkEvent & EmittedEvent
# ===========================
ChunkEventIdPath: TypeAlias = Annotated[
    EventId,
    Path(
        description="Unique identifier for the chunk event",
        examples=["bZKylRL4OP"],
    ),
]

ChunkEventSeqField: TypeAlias = Annotated[
    int,
    Field(
        description="Sequential position of the chunk",
        examples=[0, 1, 2],
        ge=0,
    ),
]

ChunkEventCreatedAtField: TypeAlias = Annotated[
    datetime,
    Field(
        description="When the session was created",
        examples=[dateutil.parser.parse("2025-01-25T22:41:41")],
    ),
]

chunk_event_example: ExampleJson = {
    "event_id": event_id_example,
    "correlation_id": correlation_id_example,
    "seq": 0,
    "patches": [{"op": "add", "path": "/-", "value": " currently"}],
    "metadata": {"agent_id": agent_id_example, "agent_name": agent_name_examples[0]},
    "timestamp": dateutil.parser.parse("2025-01-21T23:44:48").timestamp(),
}


class ChunkEventDTO(
    DefaultBaseModel,
    json_schema_extra={"example": chunk_event_example},
):
    # TODO enable once issue https://github.com/flux0-ai/flux0/issues/44 is resolved
    # id: ChunkEventIdPath
    event_id: EventIdPath
    correlation_id: EventCorrelationIdField
    seq: ChunkEventSeqField
    patches: list[JsonPatchOperationDTO]
    metadata: Mapping[str, JSONSerializableDTO]
    timestamp: float = field(default_factory=time.time)


emitted_status_event_example: ExampleJson = {
    "id": "F2srsmTGrN",
    "source": "ai_agent",
    "kind": "status",
    "correlation_id": "RID(fxjwGfAIYV)::u9ysV1pbcd",
    "data": {"type": "status", "acknowledged_offset": 0, "status": "processing", "data": {}},
}

emitted_tool_event_example: ExampleJson = {
    "correlation_id": "RID(fxjwGfAIYV)::u9ysV1pbcd",
    "event_id": "3383a5cc-3fa5-447d-8a83-85089fabf00f",
    "seq": 0,
    "patches": [
        {"op": "add", "path": "/tool_calls", "value": []},
        {"op": "replace", "path": "/tool_calls/0/tool_name", "value": "search"},
    ],
    "metadata": {},
    "timestamp": 1739376296.059654,
}

emitted_event_chunk_example: ExampleJson = {
    "correlation_id": "RID(fxjwGfAIYV)::u9ysV1pbcd",
    "event_id": "e936e0ba-1bfe-4f59-a061-2853c5517ade",
    "seq": 0,
    "patches": [{"op": "add", "path": "/content/-", "value": "Hi"}],
    "metadata": {},
    "timestamp": 1739376296.060092,
}

emitted_event_examples: ExampleJson = [
    emitted_status_event_example,
    emitted_tool_event_example,
    emitted_event_chunk_example,
]


class EmittedEventDTO(
    DefaultBaseModel,
    json_schema_extra={"examples": emitted_event_examples},
):
    id: EventIdPath
    correlation_id: EventCorrelationIdField
    type: EventTypeDTO
    source: EventSourceDTO
    # TODO at this point we don't always have an offset
    # offset: EventOffsetField
    data: Annotated[
        Union[MessageEventDataDTO, StatusEventDataDTO, ToolEventDataDTO],
        Field(discriminator="type"),
    ]
    metadata: Optional[Mapping[str, JSONSerializableDTO]] = None
    # TODO at this point nothing sets creation time
    # created_at: EventCreatedAtField


# ===========================
# Event Stream
# ===========================


class ChunkEventStream(DefaultBaseModel):
    # TODO enable once issue https://github.com/flux0-ai/flux0/issues/44 is resolved
    # id: ChunkEventIdPath
    event: Literal["chunk"]
    data: ChunkEventDTO


# NOTE: best practice would be to split these into separate models but then we move away from how persisted events look like
class EmittedEventStream(DefaultBaseModel):
    id: EventIdPath
    # event: Literal["status", "message", "tool"]
    event: Literal["status"]
    data: EmittedEventDTO


class SessionStream(RootModel[Union[ChunkEventStream, EmittedEventStream]]):
    root: Union[ChunkEventStream, EmittedEventStream] = Field(..., discriminator="event")


# ===========================
# Create Event
# ===========================

SessionEventCreationParamsContentField: TypeAlias = Annotated[
    str,
    Field(
        description="Event payload data, format depends on kind",
        examples=[user_input_content_example],
    ),
]


event_creation_params_example: ExampleJson = {
    "kind": "message",
    "source": "user",
    "content": user_input_content_example,
}


class EventCreationParamsDTO(
    DefaultBaseModel,
    json_schema_extra={"example": event_creation_params_example},
):
    """Parameters for creating a new event within a session."""

    type: EventTypeDTO
    source: EventSourceDTO
    content: Optional[SessionEventCreationParamsContentField] = None


# ===========================
# List events
# ===========================
MinOffsetQuery: TypeAlias = Annotated[
    int,
    Query(
        description="Return events with an offset greater than or equal to this value",
        examples=[0, 15],
    ),
]

CorrelationIdQuery: TypeAlias = Annotated[
    str,
    Query(
        description="ID linking related events together",
        examples=["RID(lyH-sVmwJO)::Y8oBzYT4CQ"],
    ),
]

TypesQuery: TypeAlias = Annotated[
    List[EventTypeDTO],
    Query(
        description="Filter events by specified kinds (comma-separated values)",
        examples=["message,tool", "message,custom"],
    ),
]
