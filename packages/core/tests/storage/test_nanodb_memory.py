# Fixture to provide a DocumentDatabase instance.

import pytest
from flux0_core.agents import AgentId, AgentStore, AgentType
from flux0_core.sessions import SessionStore, StatusEventData
from flux0_core.storage.nanodb_memory import (
    AgentDocumentStore,
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
    # TODO update
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
