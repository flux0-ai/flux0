# Fixture to provide a DocumentDatabase instance.

from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest
from flux0_core.agents import AgentId, AgentStore, AgentType
from flux0_core.recordings import (
    RecordedChunkPayload,
    RecordedEmittedPayload,
    RecordedEvent,
    RecordingId,
    RecordingStore,
)
from flux0_core.sessions import (
    EventId,
    MessageEventData,
    SessionId,
    SessionStatus,
    SessionStore,
    SessionUpdateParams,
    StatusEventData,
)
from flux0_core.storage.nanodb_memory import (
    AgentDocumentStore,
    RecordingDocumentStore,
    SessionDocumentStore,
    UserDocumentStore,
    _SessionDocument,
)
from flux0_core.users import UserId, UserStore
from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.memory import MemoryDocumentDatabase


@pytest.fixture
def db() -> DocumentDatabase:
    return MemoryDocumentDatabase()


# Fixture to provide a collection of TestDocument.
@pytest.fixture
async def collection(db: DocumentDatabase) -> DocumentCollection[_SessionDocument]:
    return await db.create_collection("sessions", _SessionDocument)


#############
# Agents
#############
@pytest.fixture
async def agent_store(db: DocumentDatabase) -> AgentStore:
    async with AgentDocumentStore(db) as store:
        return store


async def test_agent_crud(agent_store: AgentStore) -> None:
    # create
    #
    a = await agent_store.create_agent(name="agent1", type=AgentType("mock"))
    assert a.id is not None
    # read agent by id
    #
    ra = await agent_store.read_agent(a.id)
    assert ra == a
    # TODO update
    #
    # a.name = "agent2"
    # ra = await agent_store.update_agent(a)
    # assert ra == a
    # delete
    #
    ok = await agent_store.delete_agent(a.id)
    assert ok
    ra = await agent_store.read_agent(a.id)
    assert ra is None


#############
# Users
#############
@pytest.fixture
async def user_store(db: DocumentDatabase) -> UserStore:
    async with UserDocumentStore(db) as store:
        return store


async def test_user_crud(user_store: UserStore) -> None:
    # create
    #
    u = await user_store.create_user(sub="sub1", name="user1")
    assert u.id is not None
    # read user by id
    #
    ru = await user_store.read_user(u.id)
    assert ru == u
    # read user by sub
    #
    ru = await user_store.read_user_by_sub("sub1")
    assert ru == u
    # TODO update
    #
    # u.name = "user2"
    # ru = await user_store.update_user(u)
    # assert ru == u
    # delete
    #


#############
# Sessions
#############


@pytest.fixture
async def session_store(db: DocumentDatabase) -> SessionStore:
    async with SessionDocumentStore(db) as store:
        return store


async def test_session_crud(session_store: SessionStore) -> None:
    # create
    #
    s = await session_store.create_session(user_id=UserId("u1"), agent_id=AgentId("a1"))
    assert s.id is not None
    assert s.mode == "auto"
    # read
    #
    rs = await session_store.read_session(s.id)
    assert rs == s
    rs = await session_store.update_session(s.id, SessionUpdateParams(title="new title"))
    assert rs.title == "new title"
    rs = await session_store.read_session(s.id)
    assert rs is not None
    assert rs.title == "new title"
    # delete
    #
    ok = await session_store.delete_session(s.id)
    assert ok
    rs = await session_store.read_session(s.id)
    assert rs is None
    ok = await session_store.delete_session(s.id)
    assert not ok


async def test_session_list(session_store: SessionStore) -> None:
    # create
    #
    s1 = await session_store.create_session(user_id=UserId("u1"), agent_id=AgentId("a1"))
    s2 = await session_store.create_session(user_id=UserId("u1"), agent_id=AgentId("a2"))
    s3 = await session_store.create_session(user_id=UserId("u2"), agent_id=AgentId("a1"))
    # list
    #
    ss = await session_store.list_sessions()
    assert len(ss) == 3
    assert s1 in ss
    assert s2 in ss
    assert s3 in ss
    # list by user
    #
    ss = await session_store.list_sessions(user_id=UserId("u1"))
    assert len(ss) == 2
    assert s1 in ss
    assert s2 in ss
    assert s3 not in ss
    # list by agent
    #
    ss = await session_store.list_sessions(agent_id=AgentId("a1"))
    assert len(ss) == 2
    assert s1 in ss
    assert s2 not in ss
    assert s3 in ss
    # list by user and agent
    #
    ss = await session_store.list_sessions(user_id=UserId("u1"), agent_id=AgentId("a1"))
    assert len(ss) == 1
    assert s1 in ss
    assert s2 not in ss
    assert s3 not in ss
    # delete
    #
    ok = await session_store.delete_session(s1.id)
    assert ok
    ok = await session_store.delete_session(s2.id)
    assert ok
    ok = await session_store.delete_session(s3.id)
    assert ok
    ss = await session_store.list_sessions()
    assert len(ss) == 0


async def test_session_events_crud(session_store: SessionStore) -> None:
    # create
    #
    s = await session_store.create_session(user_id=UserId("u1"), agent_id=AgentId("a1"))
    # create event
    #
    e1 = await session_store.create_event(
        s.id,
        correlation_id="c1",
        type="status",
        source="ai_agent",
        data=StatusEventData(type="status", status="processing"),
    )
    e2 = await session_store.create_event(
        s.id,
        correlation_id="c1",
        type="status",
        source="ai_agent",
        data=StatusEventData(type="status", status="ready"),
    )
    assert e1.id is not None
    assert e2.id is not None
    # read event
    #
    re1 = await session_store.read_event(s.id, e1.id)
    assert re1 == e1
    # delete event
    #
    ok = await session_store.delete_event(e1.id)
    assert ok
    re = await session_store.read_event(s.id, e1.id)
    assert re is None
    ok = await session_store.delete_event(e1.id)
    # assert not ok
    # delete session
    #
    ok = await session_store.delete_session(s.id)
    assert ok
    rs = await session_store.read_session(s.id)
    assert rs is None
    # ensure e2 was deleted as part of session deletion
    re2 = await session_store.read_event(s.id, e2.id)
    assert re2 is None
    ok = await session_store.delete_session(s.id)
    assert not ok


async def test_session_events_list(session_store: SessionStore) -> None:
    # create
    #
    s = await session_store.create_session(user_id=UserId("u1"), agent_id=AgentId("a1"))
    # create event
    #
    e1 = await session_store.create_event(
        s.id,
        correlation_id="c1",
        type="status",
        source="ai_agent",
        data=StatusEventData(type="status", status="processing"),
    )
    e2 = await session_store.create_event(
        s.id,
        correlation_id="c1",
        type="status",
        source="ai_agent",
        data=StatusEventData(type="status", status="ready"),
    )
    # list events
    #
    es = await session_store.list_events(s.id)
    assert len(es) == 2
    assert e1 in es
    assert e2 in es
    # delete event
    #
    ok = await session_store.delete_event(e1.id)
    assert ok
    es = await session_store.list_events(s.id)
    assert len(es) == 1
    assert e1 not in es
    assert e2 in es
    # delete session
    #
    ok = await session_store.delete_session(s.id)
    assert ok
    rs = await session_store.read_session(s.id)
    assert rs is None
    # ensure e2 was deleted as part of session deletion
    es = await session_store.list_events(s.id)
    assert len(es) == 0
    ok = await session_store.delete_session(s.id)
    assert not ok


#############
# Recording
#############


@pytest.fixture
async def recording_store(db: DocumentDatabase) -> RecordingStore:
    async with RecordingDocumentStore(db) as store:
        return store


def _tz(dt: datetime) -> datetime:
    # Ensure tz-aware UTC
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _make_user_message_payload(
    correlation_id: str, msg: str, *, eid: EventId = EventId("m1")
) -> RecordedEmittedPayload:
    md: MessageEventData = {
        "type": "message",
        "participant": {"id": UserId("u1"), "name": "Anonymous"},
        "flagged": False,
        "tags": [],
        "parts": [{"type": "content", "content": msg}],
    }
    return {
        "id": eid,
        "source": "user",
        "type": "message",
        "correlation_id": correlation_id,
        "data": md,
        "metadata": {},
    }


def _make_status_payload(
    correlation_id: str, status: SessionStatus, *, eid: str = ""
) -> RecordedEmittedPayload:
    sd: StatusEventData = {"type": "status", "status": status}
    return {
        "id": EventId(eid),
        "source": "ai_agent",
        "type": "status",
        "correlation_id": correlation_id,
        "data": sd,
        "metadata": {},
    }


def _make_chunk_payload(correlation_id: str, event_id: EventId, seq: int) -> RecordedChunkPayload:
    return {
        "correlation_id": correlation_id,
        "event_id": event_id,
        "seq": seq,
        "patches": [
            {"op": "add", "path": "/-", "value": f"chunk-{seq}"},
        ],
        "metadata": {"agent_id": "A1", "agent_name": "STATIC"},
    }


# ----------------------
# Tests
# ----------------------


async def test_create_and_read_header(recording_store: RecordingStore) -> None:
    session_id = SessionId("s1")
    header = await recording_store.create_recording(
        source_session_id=session_id, created_at=_tz(datetime.now(timezone.utc))
    )

    # read by recording id
    h2 = await recording_store.read_header_by_recording_id(header.recording_id)
    assert h2 is not None
    assert h2.recording_id == header.recording_id
    assert h2.offset == 0
    assert h2.kind == "header"

    # read by source session id
    h3 = await recording_store.read_header_by_source_session_id(session_id)
    assert h3 is not None
    assert h3.recording_id == header.recording_id


async def test_append_and_order(recording_store: RecordingStore) -> None:
    session_id = SessionId("s2")
    header = await recording_store.create_recording(
        source_session_id=session_id, created_at=_tz(datetime.now(timezone.utc))
    )

    # append emitted (user message), chunk, status
    e1 = await recording_store.append_emitted(
        header.recording_id,
        _make_user_message_payload("c1", "hi"),
        created_at=_tz(datetime.now(timezone.utc)),
    )
    c1 = await recording_store.append_chunk(
        header.recording_id,
        _make_chunk_payload("c1", EventId("e1"), 0),
        created_at=_tz(datetime.now(timezone.utc) + timedelta(milliseconds=5)),
    )
    e2 = await recording_store.append_emitted(
        header.recording_id,
        _make_status_payload("c1", "completed"),
        created_at=_tz(datetime.now(timezone.utc) + timedelta(milliseconds=10)),
    )

    assert e1.offset == 1
    assert c1.offset == 2
    assert e2.offset == 3
    assert e1.created_at.tzinfo is not None and e1.created_at.utcoffset() is not None


async def test_read_next_turn_range_and_frames(recording_store: RecordingStore) -> None:
    session_id = SessionId("s3")
    h = await recording_store.create_recording(
        source_session_id=session_id, created_at=_tz(datetime.now(timezone.utc))
    )

    # Build a timeline with two user turns
    # Turn 0 start (user)
    await recording_store.append_emitted(
        h.recording_id,
        _make_user_message_payload("c1", "u0"),
        created_at=_tz(datetime.now(timezone.utc)),
    )  # off=1
    # AI status + chunk inside turn 0
    await recording_store.append_emitted(
        h.recording_id,
        _make_status_payload("c1", "processing"),
        created_at=_tz(datetime.now(timezone.utc)),
    )  # off=2
    await recording_store.append_chunk(
        h.recording_id,
        _make_chunk_payload("c1", EventId("evA"), 0),
        created_at=_tz(datetime.now(timezone.utc)),
    )  # off=3
    # Turn 1 start (user)
    await recording_store.append_emitted(
        h.recording_id,
        _make_user_message_payload("c2", "u1", eid=EventId("m2")),
        created_at=_tz(datetime.now(timezone.utc)),
    )  # off=4
    # Some more frames (ai)
    await recording_store.append_chunk(
        h.recording_id,
        _make_chunk_payload("c2", EventId("evB"), 0),
        created_at=_tz(datetime.now(timezone.utc)),
    )  # off=5

    # after=0 → first turn [1, 4)
    rng0 = await recording_store.read_next_turn_range_after_offset(h.recording_id, after_offset=0)
    assert rng0 == (1, 4)

    frames0: Sequence[RecordedEvent] = await recording_store.read_frames_range(h.recording_id, 1, 4)
    offs0 = [f.offset for f in frames0]
    assert offs0 == [1, 2, 3]

    # after=3 → next turn starts at 4, end=None
    rng1 = await recording_store.read_next_turn_range_after_offset(h.recording_id, after_offset=3)
    assert rng1 == (4, None)

    frames1: Sequence[RecordedEvent] = await recording_store.read_frames_range(
        h.recording_id, 4, None
    )
    offs1 = [f.offset for f in frames1]
    assert offs1 == [4, 5]


async def test_append_without_header_raises(recording_store: RecordingStore) -> None:
    with pytest.raises(ValueError):
        await recording_store.append_emitted(
            RecordingId("rec-missing"), _make_status_payload("c", "processing")
        )
    with pytest.raises(ValueError):
        await recording_store.append_chunk(
            RecordingId("rec-missing"), _make_chunk_payload("c", EventId("e"), 0)
        )


async def test_read_header_by_source_session_id_none(
    recording_store: RecordingStore,
) -> None:
    res = await recording_store.read_header_by_source_session_id(SessionId("nope"))
    assert res is None
