from abc import ABC, abstractmethod
from typing import Callable, Optional, Sequence, Type, TypeVar

from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent, AgentId, AgentStore, AgentType
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import Logger
from flux0_core.sessions import Event, Session, SessionId, SessionStore
from flux0_stream.emitter.api import EventEmitter


class Deps:
    def __init__(
        self,
        correlator: ContextualCorrelator,
        logger: Logger,
        event_emitter: EventEmitter,
        agent_store: AgentStore,
        session_store: SessionStore,
    ) -> None:
        self.correlator = correlator
        self.logger = logger
        self.event_emitter = event_emitter
        self._session_store = session_store
        self._agent_store = agent_store

    async def read_session(self, session_id: SessionId) -> Optional[Session]:
        return await self._session_store.read_session(session_id)

    async def list_session_events(self, session_id: SessionId) -> Sequence[Event]:
        return await self._session_store.list_events(session_id)

    async def read_agent(self, agent_id: AgentId) -> Optional[Agent]:
        return await self._agent_store.read_agent(agent_id)


class AgentRunner(ABC):
    @abstractmethod
    async def run(self, context: Context, deps: Deps) -> bool: ...


class AgentRunnerFactory(ABC):
    @abstractmethod
    def create_runner(self, agent_type: AgentType) -> AgentRunner: ...


T = TypeVar("T", bound=AgentRunner)


def agent_runner(agent: str) -> Callable[[Type[T]], Type[T]]:
    """Decorator to inject agent_type dynamically into an engine class."""

    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "agent_type", agent)
        return cls

    return decorator
