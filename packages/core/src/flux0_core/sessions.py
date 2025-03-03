from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import (
    List,
    Literal,
    Mapping,
    NewType,
    NotRequired,
    Optional,
    Sequence,
    TypeAlias,
    TypedDict,
    Union,
)

from flux0_core.agents import AgentId
from flux0_core.types import JSONSerializable
from flux0_core.users import UserId

SessionId = NewType("SessionId", str)
SessionMode: TypeAlias = Literal["auto", "manual"]


ConsumerId: TypeAlias = Literal["client"]
"""In the future we may support multiple consumer IDs"""


@dataclass(frozen=True)
class Session:
    id: SessionId
    agent_id: AgentId
    user_id: UserId
    mode: SessionMode
    title: Optional[str]
    consumption_offsets: Mapping[ConsumerId, int]
    created_at: datetime


class SessionUpdateParams(TypedDict, total=False):
    user_id: UserId
    agent_id: AgentId
    mode: SessionMode
    title: Optional[str]
    consumption_offsets: Mapping[ConsumerId, int]


EventId = NewType("EventId", str)
EventSource: TypeAlias = Literal[
    "system",
    "ai_agent",
    "user",
]
EventType: TypeAlias = Literal["message", "tool", "status", "custom"]


class Participant(TypedDict):
    id: NotRequired[AgentId | UserId | None]
    name: str


# ---- Message Parts ----
class ContentPart(TypedDict):
    type: Literal["content"]
    content: JSONSerializable


class ReasoningPart(TypedDict):
    type: Literal["reasoning"]
    reasoning: JSONSerializable


TOOL_CALL_PART_TYPE = "tool_call"
ToolCallPartType: TypeAlias = Literal["tool_call"]


class ToolCallPart(TypedDict):
    type: ToolCallPartType
    tool_call_id: str  # Used to match the tool call with the tool result
    tool_name: str
    args: JSONSerializable


# ---- Messages ----


class MessageEventData(TypedDict):
    type: Literal["message"]
    participant: Participant
    flagged: NotRequired[bool]
    tags: NotRequired[list[str]]
    parts: List[Union[ContentPart, ReasoningPart, ToolCallPart]]


# ---- Tool Call ----


class ControlOptions(TypedDict, total=False):
    mode: SessionMode


class ToolResult(TypedDict):
    data: JSONSerializable
    metadata: Mapping[str, JSONSerializable]
    control: ControlOptions


class ToolCall(TypedDict):
    tool_call_id: str  # Used to match the tool call with the tool request
    tool_name: str  # e.g., "weather_api"
    args: Mapping[str, JSONSerializable]  # args of the tool call
    result: NotRequired[ToolResult]  # Populated only if execution succeeds
    error: NotRequired[str]  # Populated only if execution fails


TOOL_CALL_RESULT_TYPE = "tool_call_result"
ToolCallResultType: TypeAlias = Literal["tool_call_result"]


class ToolEventData(TypedDict):
    type: ToolCallResultType
    tool_calls: list[ToolCall]


SessionStatus: TypeAlias = Literal[
    # The agent has acknowledged the user's message and has begun formulating a response
    "acknowledged",
    # The agent has aborted its response midway, typically due to new data being added to the session
    "cancelled",
    # The agent is assessing the session to generate a suitable response
    "processing",
    # The agent is idle and ready to accept new events
    "ready",
    # The agent has completed evaluating the session and is now generating a response
    "typing",
    # The agent has encountered an error while generating a response
    "error",
    # The agent has completed generating a response
    "completed",
]


class StatusEventData(TypedDict):
    type: Literal["status"]
    acknowledged_offset: NotRequired[int]
    status: SessionStatus
    data: NotRequired[JSONSerializable]


VALID_USER_SOURCES: set[EventSource] = {"user"}
VALID_SERVER_SOURCES: set[EventSource] = {"ai_agent"}


@dataclass(frozen=True)
class Event:
    id: EventId
    source: EventSource
    type: EventType
    offset: int
    correlation_id: str
    data: Union[MessageEventData, StatusEventData, ToolEventData]
    deleted: bool
    created_at: datetime
    metadata: Optional[Mapping[str, JSONSerializable]]


class SessionStore(ABC):
    @abstractmethod
    async def create_session(
        self,
        user_id: UserId,
        agent_id: AgentId,
        id: Optional[SessionId] = None,
        mode: Optional[SessionMode] = None,
        title: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> Session: ...

    @abstractmethod
    async def read_session(
        self,
        session_id: SessionId,
    ) -> Optional[Session]: ...

    @abstractmethod
    async def delete_session(
        self,
        session_id: SessionId,
    ) -> bool: ...

    @abstractmethod
    async def update_session(
        self,
        session_id: SessionId,
        params: SessionUpdateParams,
    ) -> Session: ...

    @abstractmethod
    async def list_sessions(
        self,
        agent_id: Optional[AgentId] = None,
        user_id: Optional[UserId] = None,
    ) -> Sequence[Session]: ...

    @abstractmethod
    async def create_event(
        self,
        session_id: SessionId,
        source: EventSource,
        type: EventType,
        correlation_id: str,
        data: Union[MessageEventData, StatusEventData, ToolEventData],
        metadata: Optional[Mapping[str, JSONSerializable]] = None,
        created_at: Optional[datetime] = None,
    ) -> Event: ...

    @abstractmethod
    async def read_event(
        self,
        session_id: SessionId,
        event_id: EventId,
    ) -> Optional[Event]: ...

    @abstractmethod
    async def delete_event(
        self,
        event_id: EventId,
    ) -> bool: ...

    @abstractmethod
    async def list_events(
        self,
        session_id: SessionId,
        source: Optional[EventSource] = None,
        correlation_id: Optional[str] = None,
        types: Sequence[EventType] = [],
        min_offset: Optional[int] = None,
        exclude_deleted: bool = True,
    ) -> Sequence[Event]: ...
