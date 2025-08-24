from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping, NewType, Optional, Sequence, Tuple, TypedDict, Union

from flux0_stream.types import JsonPatchOperation

from flux0_core.sessions import (
    EventId,
    EventSource,
    EventType,
    MessageEventData,
    SessionId,
    StatusEventData,
    ToolEventData,
)
from flux0_core.types import JSONSerializable

RecordingId = NewType("RecordingId", str)

RecordedEventId = NewType("RecordedEventId", str)


class RecordedHeaderPayload(TypedDict):
    """
    Sentinel header frame for a recording.
    Exactly one per recording at offset == 0.
    """

    source_session_id: SessionId


class RecordedChunkPayload(TypedDict):
    """Captured JSON Patch 'chunk' as sent to the client."""

    correlation_id: str
    event_id: EventId
    seq: int
    patches: list[JsonPatchOperation]
    metadata: Mapping[str, JSONSerializable]


class RecordedEmittedPayload(TypedDict):
    """Captured non-chunk event (status/message/tool/custom) as sent to the client."""

    id: EventId
    source: EventSource  # "user" | "ai_agent" | "system"
    type: EventType  # "message" | "tool" | "status" | "custom"
    correlation_id: str
    data: Union[MessageEventData, StatusEventData, ToolEventData]
    metadata: Optional[Mapping[str, JSONSerializable]]


RecordedEventKind = Literal["header", "chunk", "emitted"]
RecordedEventPayload = Union[RecordedHeaderPayload, RecordedChunkPayload, RecordedEmittedPayload]

# ── Top-level model (dataclass) persisted per frame ────────────────────────────


@dataclass(frozen=True)
class RecordedEvent:
    """
    One persisted event from a recorded stream.

    Invariants:
      • Unique (recording_id, offset)
      • Header frame: kind == "header" and offset == 0 (exactly one per recording)
      • All other frames: offset >= 1
      • created_at is the backend arrival timestamp used for pacing during replay
    """

    id: RecordedEventId  # unique identifier for this event
    recording_id: RecordingId  # identifies the recording this frame belongs to
    offset: int  # monotonic within this recording
    kind: RecordedEventKind  # "header" | "chunk" | "emitted"
    created_at: datetime  # server-arrival time for faithful pacing
    payload: RecordedEventPayload  # exact envelope originally sent to the client


TurnRange = Tuple[int, Optional[int]]  # [start, end) ; end=None → to end


class RecordingStore(ABC):
    """
    Minimal store interface for recording + interactive replay.

    Storage model:
      - Single normalized collection/table of RecordedEvent documents.
      - Exactly one header per recording at offset == 0.
      - All stream frames have offset >= 1.
      - Offsets are assigned atomically, strictly increasing per recording_id.

    Concurrency:
      - Implementations MUST assign offsets with a per-recording atomic counter.

    DB:
      - Unique: { recording_id: 1, offset: 1 }
      - Partial unique (headers): (recording_id) with filter { kind: "header", offset: 0 }
      - Lookup by session: payload.source_session_id (partial filter { kind: "header" })
      - Should support efficient querying by recording_id and offset.
    """

    # ---------- Write APIs (used while capturing a live run) ----------

    @abstractmethod
    async def create_recording(
        self,
        source_session_id: SessionId,
        *,
        recording_id: Optional[RecordingId] = None,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        """
        Create the header frame (kind='header', offset=0) for a new recording.

        Returns:
          The persisted header event.

        Must:
        - Generate a RecordingId if not provided
        - Enforce: exactly one header per recording with offset == 0
        """

    @abstractmethod
    async def append_emitted(
        self,
        recording_id: RecordingId,
        payload: RecordedEmittedPayload,
        *,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        """
        Append an 'emitted' event (status/message/tool/custom) to the recording.

        Returns:
          The persisted emitted event.

        Must:
          - Atomically assign the next monotonic offset (>= 1) per recording_id
        """

    @abstractmethod
    async def append_chunk(
        self,
        recording_id: RecordingId,
        payload: RecordedChunkPayload,
        *,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        """
        Append a 'chunk' frame (JSON Patch) to the recording.

        Must:
         - Same guarantees as append_emitted()
        """

    # ---------- Read APIs (used during interactive replay) ----------
    @abstractmethod
    async def read_header_by_source_session_id(
        self,
        source_session_id: SessionId,
    ) -> Optional[RecordedEvent]:
        """
        Fetch the header (offset == 0, kind='header') for the recording whose
        payload.source_session_id == source_session_id.

        Returns:
         -  The header RecordedEvent if exactly one exists.
          -  None if not found.

        Must:
         - avoid having multiple recordings with the same source_session_id.
        """
        ...

    @abstractmethod
    async def read_header_by_recording_id(
        self, recording_id: RecordingId
    ) -> Optional[RecordedEvent]:
        """
        Fetch the header frame (offset == 0) for a recording.
        Returns None if not found.
        """

    @abstractmethod
    async def read_next_turn_range_after_offset(
        self,
        recording_id: RecordingId,
        after_offset: int,
    ) -> Optional[TurnRange]:
        """
        Return the next USER-anchored turn that begins strictly AFTER `after_offset`.

        Semantics:
          • A turn STARTS at the next 'emitted' frame whose payload.source == 'user'.
          • A turn ENDS just before the following such user frame.
          • If there is no following user frame, end_offset_exclusive = None (stream to end).
          • Header (offset 0) is never part of a turn.

        Returns:
          • (start_offset_inclusive, end_offset_exclusive) or None if no subsequent user turn.

        Notes:
          • Pass `after_offset=0` for the very first lookup (header is at 0).
          • If you later want to narrow anchors to only user *messages*, you can
            implement the predicate as:
              kind == 'emitted' AND payload.source == 'user' AND payload.type == 'message'
            For v1, source=='user' is sufficient given your recording policy.
        """

    @abstractmethod
    async def read_frames_range(
        self,
        recording_id: RecordingId,
        start_offset_inclusive: int,
        end_offset_exclusive: Optional[int] = None,
        *,
        limit: Optional[int] = None,
    ) -> Sequence[RecordedEvent]:
        """
        Read frames ordered by offset for [start_offset_inclusive, end_offset_exclusive).
        If end_offset_exclusive is None, read to the end (respect `limit` if provided).

        Must:
          • Return frames sorted by offset ascending.
          • Exclude the header unless start_offset_inclusive == 0 (normally you'll pass >= 1).
          • Return <= limit items when 'limit' is provided.
        """
