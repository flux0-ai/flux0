from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, NewType, Optional, Sequence, TypedDict

AgentId = NewType("AgentId", str)
AgentType = NewType("AgentType", str)


@dataclass(frozen=True)
class Agent:
    id: AgentId
    type: AgentType
    name: str
    description: Optional[str]
    created_at: datetime


class AgentUpdateParams(TypedDict, total=False):
    name: str
    description: Optional[str]


class AgentStore(ABC):
    @abstractmethod
    async def create_agent(
        self,
        name: str,
        type: AgentType,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> Agent: ...

    @abstractmethod
    async def list_agents(
        self,
        offset: int = 0,
        limit: int = 10,
        projection: Optional[List[str]] = None,
    ) -> Sequence[Agent]: ...

    @abstractmethod
    async def read_agent(
        self,
        agent_id: AgentId,
    ) -> Optional[Agent]: ...

    @abstractmethod
    async def update_agent(
        self,
        agent_id: AgentId,
        params: AgentUpdateParams,
    ) -> Agent: ...

    @abstractmethod
    async def delete_agent(
        self,
        agent_id: AgentId,
    ) -> bool: ...
