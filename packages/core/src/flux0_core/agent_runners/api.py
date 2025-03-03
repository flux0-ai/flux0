from abc import ABC, abstractmethod
from typing import Callable, Type, TypeVar

from flux0_core.agent_runners.context import Context
from flux0_core.agents import AgentType
from flux0_stream.emitter.api import EventEmitter


class AgentRunner(ABC):
    @abstractmethod
    async def run(self, context: Context, event_emitter: EventEmitter) -> bool: ...


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
