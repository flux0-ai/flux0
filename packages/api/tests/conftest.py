from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from flux0_api.auth import NoopAuthHandler
from flux0_api.session_service import SessionService
from flux0_core.agent_runners.api import AgentRunner, AgentRunnerFactory, Deps
from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent, AgentId, AgentStore, AgentType
from flux0_core.background_tasks_service import BackgroundTaskService
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import ContextualLogger, Logger
from flux0_core.sessions import Session, SessionId, SessionStore
from flux0_core.storage.nanodb_memory import (
    AgentDocumentStore,
    SessionDocumentStore,
    UserDocumentStore,
)
from flux0_core.users import User, UserId, UserStore
from flux0_nanodb.api import DocumentDatabase
from flux0_nanodb.memory import MemoryDocumentDatabase
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.emitter.memory import MemoryEventEmitter
from flux0_stream.store.memory import MemoryEventStore


@pytest.fixture
def correlator() -> Generator[ContextualCorrelator]:
    c = ContextualCorrelator()
    with c.scope("test:ctx"):
        yield c


@pytest.fixture
def logger(correlator: ContextualCorrelator) -> Logger:
    return ContextualLogger(correlator=correlator)


@pytest.fixture
def user() -> User:
    return User(
        id=UserId("v9pg5Zv3h4"),
        sub="john.doe",
        name="John Doe",
        email="john.doe@acme.io",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def agent() -> Agent:
    return Agent(
        id=AgentId("vUfk4PgjTm"),
        type=AgentType("test"),
        name="Test Agent",
        description="A test agent",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def session() -> Session:
    return Session(
        id=SessionId("zv3h4j5Fjv"),
        agent_id=AgentId("vUfk4PgjTm"),
        user_id=UserId("v9pg5Zv3h4"),
        mode="auto",
        title="Test Session",
        consumption_offsets={},
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def document_db() -> AsyncGenerator[DocumentDatabase, None]:
    db = MemoryDocumentDatabase()
    yield db


@pytest.fixture
async def user_store(
    document_db: DocumentDatabase,
) -> AsyncGenerator[UserStore, None]:
    async with UserDocumentStore(db=document_db) as store:
        yield store


@pytest.fixture
async def agent_store(
    document_db: DocumentDatabase,
) -> AsyncGenerator[AgentStore, None]:
    async with AgentDocumentStore(db=document_db) as store:
        yield store


@pytest.fixture
async def session_store(
    document_db: DocumentDatabase,
) -> AsyncGenerator[SessionStore, None]:
    async with SessionDocumentStore(db=document_db) as store:
        yield store


@pytest.fixture
def background_task_service(logger: Logger) -> BackgroundTaskService:
    return BackgroundTaskService(logger=logger)


# Dummy implementation of AgentRunner
class DummyAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        return True


# Modified factory that allows injecting custom AgentRunner implementations
class MockAgentRunnerFactory(AgentRunnerFactory):
    def __init__(self, runner_class: type[AgentRunner] = DummyAgentRunner) -> None:
        self.runner_class = runner_class  # Allow injecting different runner classes

    def create_runner(self, agent_type: AgentType) -> AgentRunner:
        return self.runner_class()  # Instantiate the injected runner


@pytest.fixture
def agent_runner_factory() -> AgentRunnerFactory:
    return MockAgentRunnerFactory()


@pytest.fixture
async def event_emitter(logger: Logger) -> AsyncGenerator[EventEmitter, None]:
    """Provide a properly initialized EventEmitter instance using AsyncExitStack for clean resource management."""

    async with AsyncExitStack() as stack:
        store = await stack.enter_async_context(MemoryEventStore())
        emitter = await stack.enter_async_context(
            MemoryEventEmitter(event_store=store, logger=logger)
        )

        yield emitter


@pytest.fixture
def session_service(
    correlator: ContextualCorrelator,
    logger: Logger,
    session_store: SessionStore,
    agent_store: AgentStore,
    background_task_service: BackgroundTaskService,
    agent_runner_factory: AgentRunnerFactory,
    event_emitter: EventEmitter,
) -> SessionService:
    return SessionService(
        contextual_correlator=correlator,
        logger=logger,
        agent_store=agent_store,
        session_store=session_store,
        background_task_service=background_task_service,
        agent_runner_factory=agent_runner_factory,
        event_emitter=event_emitter,
    )


@pytest.fixture
def fastapi(
    correlator: ContextualCorrelator, user_store: UserStore, session_service: SessionService
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.auth_handler = NoopAuthHandler(user_store=user_store)
        app.state.user_store = user_store
        app.state.session_service = session_service
        yield

    app = FastAPI(lifespan=lifespan)

    return app
