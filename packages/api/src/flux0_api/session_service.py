from datetime import datetime, timezone
from typing import Optional, Union

from flux0_core.agent_runners.api import AgentRunnerFactory
from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent
from flux0_core.background_tasks_service import BackgroundTaskService
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id
from flux0_core.sessions import (
    Event,
    EventSource,
    EventType,
    MessageEventData,
    Session,
    SessionId,
    SessionStore,
    StatusEventData,
    ToolEventData,
)
from flux0_core.users import UserId
from flux0_stream.emitter.api import EventEmitter


class SessionService:
    def __init__(
        self,
        contextual_correlator: ContextualCorrelator,
        session_store: SessionStore,
        background_task_service: BackgroundTaskService,
        agent_runner_factory: AgentRunnerFactory,
        event_emitter: EventEmitter,
    ):
        self._correlator = contextual_correlator
        self._session_store = session_store
        self._background_task_service = background_task_service
        self._agent_runner_factory = agent_runner_factory
        self._event_emitter = event_emitter

    async def create_user_session(
        self,
        user_id: UserId,
        agent: Agent,
        id: Optional[SessionId] = None,
        title: Optional[str] = None,
        allow_greeting: bool = False,
    ) -> Session:
        session = await self._session_store.create_session(
            user_id=user_id,
            agent_id=agent.id,
            id=id,
            title=title,
            created_at=datetime.now(timezone.utc),
        )

        if allow_greeting:
            await self.dispatch_processing_task(session, agent)

        return session

    async def dispatch_processing_task(
        self, session: Session, agent: Agent, correlation_id: Optional[str] = None
    ) -> str:
        if correlation_id is None:
            with self._correlator.scope(gen_id()):
                correlation_id = self._correlator.correlation_id

        await self._background_task_service.restart(
            self._process_session(session, agent),
            tag=f"process-session({session.id})",
        )

        return self._correlator.correlation_id

    async def cancel_processing_session_task(self, session_id: SessionId) -> None:
        await self._background_task_service.cancel(
            tag=f"process-session({session_id})", reason="user-cancel"
        )

    async def post_event(
        self,
        session: Session,
        agent: Agent,
        type: EventType,
        data: Union[MessageEventData, StatusEventData, ToolEventData],
        source: EventSource = "user",
        trigger_processing: bool = True,
    ) -> Event:
        if trigger_processing:
            with self._correlator.scope(gen_id()):
                event = await self._session_store.create_event(
                    session_id=session.id,
                    source=source,
                    type=type,
                    correlation_id=self._correlator.correlation_id,
                    data=data,
                )
                await self.dispatch_processing_task(session, agent, self._correlator.correlation_id)
        else:
            event = await self._session_store.create_event(
                session_id=session.id,
                source=source,
                type=type,
                correlation_id=self._correlator.correlation_id,
                data=data,
            )

        return event

    async def _process_session(self, session: Session, agent: Agent) -> None:
        runner = self._agent_runner_factory.create_runner(agent.type)
        await runner.run(
            Context(
                session_id=session.id,
                agent_id=session.agent_id,
            ),
            event_emitter=self._event_emitter,
        )
