import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Mapping, Optional, Self, Sequence, Union, override

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
from flux0_nanodb.types import Document, DocumentID, DocumentVersion


#############
# User
#############
@dataclass(frozen=True)
class _UserDocument(User, Document):
    version: DocumentVersion


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
        data = asdict(user)
        data["id"] = DocumentID(user.id)
        data["version"] = self.VERSION
        return _UserDocument(**data)

    def _deserialize_user(
        self,
        doc: _UserDocument,
    ) -> User:
        data = asdict(doc)
        data.pop("version")
        data["id"] = UserId(doc.id)
        return User(**data)

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
@dataclass(frozen=True)
class _AgentDocument(Agent, Document):
    version: DocumentVersion


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
        data = asdict(agent)
        data["id"] = DocumentID(agent.id)
        data["version"] = self.VERSION
        return _AgentDocument(**data)

    def _deserialize_agent(
        self,
        doc: _AgentDocument,
    ) -> Agent:
        data = asdict(doc)
        data.pop("version")
        data["id"] = AgentId(doc.id)
        return Agent(**data)

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


@dataclass(frozen=True)
class _SessionDocument(Session, Document):
    version: DocumentVersion


@dataclass(frozen=True)
class _EventDocument(Event, Document):
    version: DocumentVersion
    session_id: SessionId


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
        data = asdict(session)
        data["id"] = DocumentID(session.id)
        data["version"] = self.VERSION
        return _SessionDocument(**data)

    def _deserialize_session(
        self,
        doc: _SessionDocument,
    ) -> Session:
        data = asdict(doc)
        data.pop("version")
        data["id"] = SessionId(doc.id)
        return Session(**data)

    def _serialize_event(
        self,
        session_id: SessionId,
        event: Event,
    ) -> _EventDocument:
        data = asdict(event)
        data["id"] = DocumentID(event.id)
        data["session_id"] = DocumentID(session_id)
        data["version"] = self.VERSION
        return _EventDocument(**data)

    def _deserialize_event(
        self,
        doc: _EventDocument,
    ) -> Event:
        data = asdict(doc)
        data.pop("version")
        data.pop("session_id")
        data["id"] = EventId(doc.id)
        return Event(**data)

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
