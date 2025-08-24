import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    DefaultDict,
    List,
    Mapping,
    Optional,
    Required,
    Self,
    Sequence,
    TypedDict,
    Union,
    override,
)

from flux0_core.agents import Agent, AgentId, AgentStore, AgentType, AgentUpdateParams
from flux0_core.ids import gen_id
from flux0_core.recordings import (
    RecordedChunkPayload,
    RecordedEmittedPayload,
    RecordedEvent,
    RecordedEventId,
    RecordedEventKind,
    RecordedEventPayload,
    RecordedHeaderPayload,
    RecordingId,
    RecordingStore,
    TurnRange,
)
from flux0_core.sessions import (
    ConsumerId,
    Event,
    EventId,
    EventSource,
    EventType,
    MessageEventData,
    Session,
    SessionId,
    SessionMode,
    SessionStore,
    SessionUpdateParams,
    StatusEventData,
    ToolEventData,
)
from flux0_core.types import JSONSerializable
from flux0_core.users import User, UserId, UserStore, UserUpdateParams
from flux0_nanodb import projection
from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.query import And, Comparison, QueryFilter
from flux0_nanodb.types import DocumentID, DocumentVersion, JSONPatchOperation, SortingOrder


#############
# User
#############
class _UserDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    sub: str
    name: str
    email: Optional[str]
    created_at: datetime


class UserDocumentStore(UserStore):
    VERSION = DocumentVersion("0.0.1")

    def __init__(self, db: DocumentDatabase):
        self.db = db
        self._user_col: DocumentCollection[_UserDocument]

    async def __aenter__(self) -> Self:
        self._user_col = await self.db.create_collection("users", _UserDocument)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exec_tb: Optional[object],
    ) -> None:
        pass

    def _serialize_user(
        self,
        user: User,
    ) -> _UserDocument:
        return _UserDocument(
            id=DocumentID(user.id),
            version=self.VERSION,
            sub=user.sub,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
        )

    def _deserialize_user(
        self,
        doc: _UserDocument,
    ) -> User:
        return User(
            id=UserId(doc["id"]),
            sub=doc["sub"],
            name=doc["name"],
            email=doc.get("email"),
            created_at=doc["created_at"],
        )

    @override
    async def create_user(
        self,
        sub: str,
        name: str,
        email: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> User:
        created_at = created_at or datetime.now(timezone.utc)
        user = User(
            id=UserId(gen_id()),
            sub=sub,
            name=name,
            email=email,
            created_at=created_at,
        )
        await self._user_col.insert_one(document=self._serialize_user(user))
        return user

    @override
    async def read_user(
        self,
        user_id: UserId,
    ) -> Optional[User]:
        result = await self._user_col.find(Comparison(path="id", op="$eq", value=user_id))
        return self._deserialize_user(result[0]) if result else None

    @override
    async def read_user_by_sub(
        self,
        sub: str,
    ) -> Optional[User]:
        result = await self._user_col.find(Comparison(path="sub", op="$eq", value=sub))
        return self._deserialize_user(result[0]) if result else None

    @override
    async def update_user(
        self,
        user_id: UserId,
        params: UserUpdateParams,
    ) -> User:
        raise NotImplementedError


#############
# Agent
#############
class _AgentDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    type: AgentType
    name: str
    description: Optional[str]
    created_at: datetime


class AgentDocumentStore(AgentStore):
    VERSION = DocumentVersion("0.0.1")

    def __init__(self, db: DocumentDatabase):
        self.db = db
        self._agent_col: DocumentCollection[_AgentDocument]

    async def __aenter__(self) -> Self:
        self._agent_col = await self.db.create_collection("agents", _AgentDocument)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exec_tb: Optional[object],
    ) -> None:
        pass

    def _serialize_agent(
        self,
        agent: Agent,
    ) -> _AgentDocument:
        return _AgentDocument(
            id=DocumentID(agent.id),
            version=self.VERSION,
            type=agent.type,
            name=agent.name,
            description=agent.description,
            created_at=agent.created_at,
        )

    def _deserialize_agent(
        self,
        doc: _AgentDocument,
    ) -> Agent:
        return Agent(
            id=AgentId(doc["id"]),
            type=doc["type"],
            name=doc["name"],
            description=doc["description"],
            created_at=doc["created_at"],
        )

    @override
    async def create_agent(
        self,
        name: str,
        type: AgentType,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> Agent:
        created_at = created_at or datetime.now(timezone.utc)
        agent = Agent(
            id=AgentId(gen_id()),
            name=name,
            type=type,
            description=description,
            created_at=created_at,
        )
        await self._agent_col.insert_one(document=self._serialize_agent(agent))
        return agent

    @override
    async def read_agent(
        self,
        agent_id: AgentId,
    ) -> Optional[Agent]:
        result = await self._agent_col.find(Comparison(path="id", op="$eq", value=agent_id))
        return self._deserialize_agent(result[0]) if result else None

    @override
    async def list_agents(
        self,
        offset: int = 0,
        limit: int = 10,
        projection: Optional[List[str]] = None,
    ) -> Sequence[Agent]:
        if offset != 0 or limit != 10:
            raise NotImplementedError("Pagination is not supported")
        if projection is not None:
            raise NotImplementedError("Projection not supported")
        return [self._deserialize_agent(d) for d in await self._agent_col.find(filters=None)]

    @override
    async def update_agent(
        self,
        agent_id: AgentId,
        params: AgentUpdateParams,
    ) -> Agent:
        raise NotImplementedError

    @override
    async def delete_agent(
        self,
        agent_id: AgentId,
    ) -> bool:
        result = await self._agent_col.delete_one(Comparison(path="id", op="$eq", value=agent_id))
        return result.deleted_count > 0


#############
# Session
#############


class _SessionDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    agent_id: AgentId
    user_id: UserId
    mode: SessionMode
    title: Optional[str]
    consumption_offsets: Mapping[ConsumerId, int]
    created_at: datetime
    metadata: Optional[Mapping[str, JSONSerializable]]


@dataclass(frozen=True)
class _EventDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    session_id: SessionId
    source: EventSource
    type: EventType
    offset: int
    correlation_id: str
    data: Union[MessageEventData, StatusEventData, ToolEventData]
    deleted: bool
    created_at: datetime
    metadata: Optional[Mapping[str, JSONSerializable]]


class SessionDocumentStore(SessionStore):
    VERSION = DocumentVersion("0.0.1")

    def __init__(self, db: DocumentDatabase):
        self.db = db
        self._session_col: DocumentCollection[_SessionDocument]
        self._event_col: DocumentCollection[_EventDocument]

    async def __aenter__(self) -> Self:
        self._session_col = await self.db.create_collection("sessions", _SessionDocument)
        self._event_col = await self.db.create_collection("session_events", _EventDocument)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exec_tb: Optional[object],
    ) -> None:
        pass

    def _serialize_session(
        self,
        session: Session,
    ) -> _SessionDocument:
        return _SessionDocument(
            id=DocumentID(session.id),
            version=self.VERSION,
            agent_id=session.agent_id,
            user_id=session.user_id,
            mode=session.mode,
            title=session.title,
            consumption_offsets=session.consumption_offsets,
            created_at=session.created_at,
            metadata=session.metadata,
        )

    def _deserialize_session(
        self,
        doc: _SessionDocument,
    ) -> Session:
        return Session(
            id=SessionId(doc["id"]),
            agent_id=doc["agent_id"],
            user_id=doc["user_id"],
            mode=doc["mode"],
            title=doc.get("title"),
            consumption_offsets=doc["consumption_offsets"],
            created_at=doc["created_at"],
            metadata=doc.get("metadata", None),
        )

    def _serialize_event(
        self,
        session_id: SessionId,
        event: Event,
    ) -> _EventDocument:
        return _EventDocument(
            id=DocumentID(event.id),
            version=self.VERSION,
            session_id=session_id,
            source=event.source,
            type=event.type,
            offset=event.offset,
            correlation_id=event.correlation_id,
            data=event.data,
            deleted=event.deleted,
            created_at=event.created_at,
            metadata=event.metadata,
        )

    def _deserialize_event(
        self,
        doc: _EventDocument,
    ) -> Event:
        return Event(
            id=EventId(doc["id"]),
            source=doc["source"],
            type=doc["type"],
            offset=doc["offset"],
            correlation_id=doc["correlation_id"],
            data=doc["data"],
            deleted=doc["deleted"],
            created_at=doc["created_at"],
            metadata=doc.get("metadata"),
        )

    @override
    async def create_session(
        self,
        user_id: UserId,
        agent_id: AgentId,
        id: Optional[SessionId] = None,
        mode: Optional[SessionMode] = None,
        title: Optional[str] = None,
        metadata: Optional[Mapping[str, JSONSerializable]] = None,
        created_at: Optional[datetime] = None,
    ) -> Session:
        created_at = created_at or datetime.now(timezone.utc)
        consumption_offsets: dict[ConsumerId, int] = {"client": 0}
        session = Session(
            id=id or SessionId(gen_id()),
            user_id=user_id,
            agent_id=agent_id,
            mode=mode or "auto",
            title=title,
            consumption_offsets=consumption_offsets,
            created_at=created_at,
            metadata=metadata,
        )
        await self._session_col.insert_one(document=self._serialize_session(session))
        return session

    @override
    async def read_session(
        self,
        session_id: SessionId,
    ) -> Optional[Session]:
        result = await self._session_col.find(Comparison(path="id", op="$eq", value=session_id))
        return self._deserialize_session(result[0]) if result else None

    @override
    async def delete_session(
        self,
        session_id: SessionId,
    ) -> bool:
        # delete events
        events = await self.list_events(session_id)
        # for event in events:
        futures = [
            asyncio.ensure_future(
                self._event_col.delete_one(Comparison(path="id", op="$eq", value=e.id))
            )
            for e in events
        ]
        await asyncio.gather(*futures, return_exceptions=False)

        # delete session
        result = await self._session_col.delete_one(
            Comparison(path="id", op="$eq", value=session_id)
        )
        return result.deleted_count > 0

    @override
    async def update_session(
        self,
        session_id: SessionId,
        params: SessionUpdateParams,
    ) -> Session:
        update_data = {k: v for k, v in params.items() if v is not None}
        patch: List[JSONPatchOperation] = [
            {"op": "replace", "path": f"/{k}", "value": v} for k, v in update_data.items()
        ]
        await self._session_col.update_one(Comparison(path="id", op="$eq", value=session_id), patch)
        updated = await self.read_session(session_id)
        if not updated:
            raise ValueError(f"Session not found: {session_id}")
        return updated

    @override
    async def list_sessions(
        self,
        agent_id: Optional[AgentId] = None,
        user_id: Optional[UserId] = None,
    ) -> Sequence[Session]:
        expressions: List[QueryFilter] = []

        if agent_id is not None:
            expressions.append(Comparison(path="agent_id", op="$eq", value=str(agent_id)))

        if user_id is not None:
            expressions.append(Comparison(path="user_id", op="$eq", value=str(user_id)))

        query_filter: Optional[QueryFilter] = None
        if expressions:
            query_filter = And(expressions=expressions)

        return [self._deserialize_session(d) for d in await self._session_col.find(query_filter)]

    @override
    async def create_event(
        self,
        session_id: SessionId,
        source: EventSource,
        type: EventType,
        correlation_id: str,
        data: Union[MessageEventData, StatusEventData, ToolEventData],
        metadata: Optional[Mapping[str, JSONSerializable]] = None,
        created_at: Optional[datetime] = None,
    ) -> Event:
        session = await self.read_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        events = await self.list_events(session_id)
        offset = len(list(events))

        created_at = created_at or datetime.now(timezone.utc)
        event = Event(
            id=EventId(gen_id()),
            source=source,
            type=type,
            offset=offset,
            correlation_id=correlation_id,
            data=data,
            metadata=metadata,
            deleted=False,
            created_at=created_at,
        )
        await self._event_col.insert_one(document=self._serialize_event(session_id, event))
        return event

    @override
    async def read_event(
        self,
        session_id: SessionId,
        event_id: EventId,
    ) -> Optional[Event]:
        result = await self._event_col.find(
            And(
                expressions=[
                    Comparison(path="id", op="$eq", value=event_id),
                    Comparison(path="session_id", op="$eq", value=session_id),
                ]
            )
        )
        return self._deserialize_event(result[0]) if result else None

    @override
    async def delete_event(
        self,
        event_id: EventId,
    ) -> bool:
        result = await self._event_col.delete_one(Comparison(path="id", op="$eq", value=event_id))
        return result.deleted_count > 0

    @override
    async def list_events(
        self,
        session_id: SessionId,
        source: Optional[EventSource] = None,
        correlation_id: Optional[str] = None,
        types: Sequence[EventType] = [],
        min_offset: Optional[int] = None,
        exclude_deleted: bool = True,
    ) -> Sequence[Event]:
        expressions: List[QueryFilter] = [Comparison(path="session_id", op="$eq", value=session_id)]

        if source is not None:
            expressions.append(Comparison(path="source", op="$eq", value=source))

        if correlation_id is not None:
            expressions.append(Comparison(path="correlation_id", op="$eq", value=correlation_id))

        if types:
            expressions.append(Comparison(path="type", op="$in", value=list(types)))

        if min_offset is not None:
            expressions.append(Comparison(path="offset", op="$gte", value=min_offset))

        if exclude_deleted:
            expressions.append(Comparison(path="deleted", op="$eq", value=False))

        query_filter: Optional[QueryFilter] = None
        if expressions:
            query_filter = And(expressions=expressions)

        return [self._deserialize_event(d) for d in await self._event_col.find(query_filter)]


#############
# Recording
#############


@dataclass(frozen=True)
class _RecordedEventDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    recording_id: Required[RecordingId]
    offset: Required[int]
    kind: Required[RecordedEventKind]
    created_at: Required[datetime]
    payload: Required[RecordedEventPayload]


class RecordingDocumentStore(RecordingStore):
    VERSION = DocumentVersion("0.0.1")

    def __init__(self, db: DocumentDatabase):
        self.db = db
        self._col: DocumentCollection[_RecordedEventDocument]
        self._locks: dict[RecordingId, asyncio.Lock] = DefaultDict(asyncio.Lock)

    async def __aenter__(self) -> Self:
        self._col = await self.db.create_collection("recorded_events", _RecordedEventDocument)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exec_tb: Optional[object],
    ) -> None:
        pass

    def _serialize(self, ev: RecordedEvent) -> _RecordedEventDocument:
        return _RecordedEventDocument(
            id=DocumentID(ev.id),
            recording_id=ev.recording_id,
            version=self.VERSION,
            offset=ev.offset,
            kind=ev.kind,
            created_at=ev.created_at,
            payload=ev.payload,  # TypedDicts are JSON-serializable
        )

    def _deserialize(self, doc: _RecordedEventDocument) -> RecordedEvent:
        return RecordedEvent(
            id=RecordedEventId(doc["id"]),
            recording_id=RecordingId(doc["recording_id"]),
            offset=doc["offset"],
            kind=doc["kind"],
            created_at=doc["created_at"],
            payload=doc["payload"],
        )

    # In-process (nanodb / single worker): guard with an asyncio.Lock per recording_id.
    # TODO: Cross-process (Mongo): use an atomic counter (e.g., findOneAndUpdate + $inc) or rely on a unique index on (recording_id, offset) and retry on duplicate key.
    # TODO: Instead of reading all docs, ask the DB for one sorted desc by offset (e.g., sort=[("offset", -1)], return (last["offset"] + 1) if last else 1)
    async def _next_offset(self, recording_id: RecordingId) -> int:
        # Find max offset for this recording_id and return +1
        docs = await self._col.find(Comparison(path="recording_id", op="$eq", value=recording_id))
        return (max(d["offset"] for d in docs) + 1) if docs else 1

    async def _ensure_header_exists(self, recording_id: RecordingId) -> None:
        header = await self.read_header_by_recording_id(recording_id)
        if header is None:
            raise ValueError(f"Recording header not found for {recording_id}")

    @override
    async def create_recording(
        self,
        source_session_id: SessionId,
        *,
        recording_id: Optional[RecordingId] = None,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        rid = recording_id or RecordingId(gen_id())
        created_at = created_at or datetime.now(timezone.utc)

        header_payload: RecordedHeaderPayload = {
            "source_session_id": source_session_id,
        }
        header = RecordedEvent(
            id=RecordedEventId(gen_id()),
            recording_id=rid,
            offset=0,
            kind="header",
            created_at=created_at,
            payload=header_payload,
        )
        await self._col.insert_one(self._serialize(header))
        return header

    @override
    async def append_emitted(
        self,
        recording_id: RecordingId,
        payload: RecordedEmittedPayload,
        *,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        await self._ensure_header_exists(recording_id)
        created_at = created_at or datetime.now(timezone.utc)
        async with self._locks[recording_id]:
            offset = await self._next_offset(recording_id)
            ev = RecordedEvent(
                id=RecordedEventId(gen_id()),
                recording_id=recording_id,
                offset=offset,
                kind="emitted",
                created_at=created_at,
                payload=payload,
            )
            await self._col.insert_one(self._serialize(ev))
        return ev

    @override
    async def append_chunk(
        self,
        recording_id: RecordingId,
        payload: RecordedChunkPayload,
        *,
        created_at: Optional[datetime] = None,
    ) -> RecordedEvent:
        await self._ensure_header_exists(recording_id)
        created_at = created_at or datetime.now(timezone.utc)
        offset = await self._next_offset(recording_id)
        ev = RecordedEvent(
            id=RecordedEventId(gen_id()),
            recording_id=recording_id,
            offset=offset,
            kind="chunk",
            created_at=created_at,
            payload=payload,
        )
        await self._col.insert_one(self._serialize(ev))
        return ev

    @override
    async def read_header_by_source_session_id(
        self,
        source_session_id: SessionId,
    ) -> Optional[RecordedEvent]:
        result = await self._col.find(
            And(
                expressions=[
                    Comparison(path="kind", op="$eq", value="header"),
                    Comparison(path="payload.source_session_id", op="$eq", value=source_session_id),
                    Comparison(path="offset", op="$eq", value=0),
                ]
            )
        )
        return self._deserialize(result[0]) if result else None

    @override
    async def read_header_by_recording_id(
        self, recording_id: RecordingId
    ) -> Optional[RecordedEvent]:
        docs = await self._col.find(
            # header is unique (offset == 0) — any one match is fine
            # Using both conditions keeps invariants clear
            And(
                expressions=[
                    Comparison(path="recording_id", op="$eq", value=recording_id),
                    Comparison(path="offset", op="$eq", value=0),
                    Comparison(path="kind", op="$eq", value="header"),
                ]
            )
        )
        return self._deserialize(docs[0]) if docs else None

    @override
    async def read_next_turn_range_after_offset(
        self,
        recording_id: RecordingId,
        after_offset: int,
    ) -> Optional[TurnRange]:
        """
        Return the next user-anchored turn that begins strictly AFTER `after_offset`.
        A "user anchor" is: kind=='emitted' AND payload.source=='user'.
        """

        # 1) Find the FIRST user anchor with document.offset > after_offset
        start_docs = await self._col.find(
            And(
                expressions=[
                    Comparison(path="recording_id", op="$eq", value=recording_id),
                    Comparison(path="kind", op="$eq", value="emitted"),
                    Comparison(path="payload.source", op="$eq", value="user"),
                    Comparison(path="offset", op="$gt", value=after_offset),
                ]
            ),
            # Only need 'offset' to compute the range; keeps IO small
            projection={
                "offset": projection.Projection.INCLUDE
            },  # or 1, depending on your Projection type
            limit=1,
            sort=[("offset", SortingOrder.ASC)],
        )
        if not start_docs:
            return None
        start = start_docs[0]["offset"]

        # 2) Find the NEXT user anchor strictly after `start` to bound the range
        next_docs = await self._col.find(
            And(
                expressions=[
                    Comparison(path="recording_id", op="$eq", value=recording_id),
                    Comparison(path="kind", op="$eq", value="emitted"),
                    Comparison(path="payload.source", op="$eq", value="user"),
                    Comparison(path="offset", op="$gt", value=start),
                ]
            ),
            projection={"offset": projection.Projection.INCLUDE},
            limit=1,
            sort=[("offset", SortingOrder.ASC)],
        )
        end = next_docs[0]["offset"] if next_docs else None
        return (start, end)

    @override
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
        """
        filters: list[QueryFilter] = [
            Comparison(path="recording_id", op="$eq", value=recording_id),
            Comparison(path="offset", op="$gte", value=start_offset_inclusive),
        ]
        if end_offset_exclusive is not None:
            filters.append(Comparison(path="offset", op="$lt", value=end_offset_exclusive))

        docs = await self._col.find(
            And(expressions=filters),
            # We need full docs for replay (payload, created_at, etc.), so no projection
            limit=limit,
            sort=[("offset", SortingOrder.ASC)],
        )
        # Defensive: DB already sorted; keep in case backend changes
        # docs.sort(key=lambda d: d["offset"])
        return [self._deserialize(d) for d in docs]
