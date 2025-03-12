import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Mapping, Optional, Self, Sequence, TypedDict, Union, override

from flux0_core.agents import Agent, AgentId, AgentStore, AgentType, AgentUpdateParams
from flux0_core.async_utils import RWLock
from flux0_core.ids import gen_id
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
from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.query import And, Comparison, QueryFilter
from flux0_nanodb.types import DocumentID, DocumentVersion


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
        self._lock = RWLock()

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
        async with self._lock.writer_lock:
            await self._user_col.insert_one(document=self._serialize_user(user))
        return user

    @override
    async def read_user(
        self,
        user_id: UserId,
    ) -> Optional[User]:
        async with self._lock.reader_lock:
            result = await self._user_col.find(Comparison(path="id", op="$eq", value=user_id))
            return self._deserialize_user(result[0]) if result else None

    @override
    async def read_user_by_sub(
        self,
        sub: str,
    ) -> Optional[User]:
        async with self._lock.reader_lock:
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
        self._lock = RWLock()

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
        async with self._lock.writer_lock:
            await self._agent_col.insert_one(document=self._serialize_agent(agent))
        return agent

    @override
    async def read_agent(
        self,
        agent_id: AgentId,
    ) -> Optional[Agent]:
        async with self._lock.reader_lock:
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
        async with self._lock.reader_lock:
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
        async with self._lock.writer_lock:
            result = await self._agent_col.delete_one(
                Comparison(path="id", op="$eq", value=agent_id)
            )
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
        self._lock = RWLock()

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
        )
        async with self._lock.writer_lock:
            await self._session_col.insert_one(document=self._serialize_session(session))
        return session

    @override
    async def read_session(
        self,
        session_id: SessionId,
    ) -> Optional[Session]:
        async with self._lock.reader_lock:
            result = await self._session_col.find(Comparison(path="id", op="$eq", value=session_id))
            return self._deserialize_session(result[0]) if result else None

    @override
    async def delete_session(
        self,
        session_id: SessionId,
    ) -> bool:
        async with self._lock.writer_lock:
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
        raise NotImplementedError

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

        async with self._lock.reader_lock:
            return [
                self._deserialize_session(d) for d in await self._session_col.find(query_filter)
            ]

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
        async with self._lock.writer_lock:
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
        async with self._lock.reader_lock:
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
        async with self._lock.writer_lock:
            result = await self._event_col.delete_one(
                Comparison(path="id", op="$eq", value=event_id)
            )
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

        async with self._lock.reader_lock:
            return [self._deserialize_event(d) for d in await self._event_col.find(query_filter)]
