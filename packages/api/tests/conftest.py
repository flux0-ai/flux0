from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from flux0_api.auth import AuthHandler, NoopAuthHandler
from flux0_api.session_service import SessionService
from flux0_core.agent_runners.api import AgentRunner, AgentRunnerFactory
from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent, AgentId, AgentStore, AgentType
from flux0_core.background_tasks_service import BackgroundTaskService
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import ILogger, Logger
from flux0_core.sessions import SessionStore
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
from lagom import Container


@pytest.fixture
def correlator() -> ContextualCorrelator:
    return ContextualCorrelator()


@pytest.fixture
def logger(correlator: ContextualCorrelator) -> ILogger:
    return Logger(correlator=correlator)


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
        id=AgentId("1q2w3e4r5t"),
        type=AgentType("test"),
        name="Test Agent",
        description="A test agent",
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
def background_task_service(logger: ILogger) -> BackgroundTaskService:
    return BackgroundTaskService(logger=logger)


# Dummy implementation of AgentRunner
class DummyAgentRunner(AgentRunner):
    async def run(self, context: Context, event_emitter: EventEmitter) -> bool:
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
    session_store: SessionStore,
    background_task_service: BackgroundTaskService,
    agent_runner_factory: AgentRunnerFactory,
    event_emitter: EventEmitter,
) -> SessionService:
    return SessionService(
        contextual_correlator=correlator,
        session_store=session_store,
        background_task_service=background_task_service,
        agent_runner_factory=agent_runner_factory,
        event_emitter=event_emitter,
    )


@pytest.fixture
def container(
    correlator: ContextualCorrelator, user_store: UserStore, session_service: SessionService
) -> Container:
    c = Container()
    c[ContextualCorrelator] = correlator
    c[UserStore] = user_store
    c[SessionService] = session_service
    c[AuthHandler] = NoopAuthHandler
    return c


@pytest.fixture
def fastapi(container: Container) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.container = container
        yield

    app = FastAPI(lifespan=lifespan)

    return app
