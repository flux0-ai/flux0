from dataclasses import dataclass
from typing import Sequence

from flux0_core.agents import AgentId
from flux0_core.sessions import Event, SessionId


@dataclass(frozen=True)
class Context:
    session_id: SessionId
    agent_id: AgentId


@dataclass(frozen=True)
class InteractionState:
    last_known_event_offset: int
    history: Sequence[Event]
