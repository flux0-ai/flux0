import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from flux0_api.session_service import SessionService
from flux0_api.sessions import (
    mount_create_event_and_stream_route,
    mount_create_session_route,
    mount_get_session_route,
    mount_list_session_events_route,
)
from flux0_api.types_events import (
    ContentPartDTO,
    EventCreationParamsDTO,
    EventDTO,
    EventSourceDTO,
    EventTypeDTO,
    MessageEventDataDTO,
)
from flux0_api.types_session import SessionCreationParamsDTO, SessionDTO
from flux0_core.agent_runners.api import AgentRunner
from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent, AgentId, AgentStore
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id
from flux0_core.sessions import (
    ContentPart,
    EventId,
    MessageEventData,
    Participant,
    Session,
    SessionId,
    SessionStore,
    StatusEventData,
)
from flux0_core.users import User, UserStore
from flux0_stream.emitter.api import EventEmitter

from .conftest import MockAgentRunnerFactory


async def test_create_session_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    session_service: SessionService,
) -> None:
    agent = await agent_store.create_agent(
        name=agent.name, type=agent.type, description=agent.description
    )

    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_session_route = mount_create_session_route(router, user, agent_store, session_service)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session")
    result: SessionDTO = await create_session_route(params, False)

    # Assert the returned session has expected values.
    assert result.id is not None
    assert result.agent_id == agent.id
    # assert result.user_id == "user123"
    assert result.title == "Test session"
    # Check that the consumption_offsets is set correctly.
    assert result.consumption_offsets.client == 0

    assert result.created_at < datetime.now(timezone.utc)


async def test_create_session_with_greeting_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    session_service: SessionService,
) -> None:
    class MockAgentRunner(AgentRunner):
        run = AsyncMock(return_value=True)

    session_service._agent_runner_factory = MockAgentRunnerFactory(runner_class=MockAgentRunner)
    agent = await agent_store.create_agent(
        name=agent.name, type=agent.type, description=agent.description
    )

    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_session_route = mount_create_session_route(router, user, agent_store, session_service)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session")
    result: SessionDTO = await create_session_route(params, True)

    # Assert the returned session has expected values.
    assert result.id is not None
    assert result.agent_id == agent.id
    assert result.user_id == user.id
    assert result.title == "Test session"
    # Check that the consumption_offsets is set correctly.
    assert result.consumption_offsets.client == 0

    assert result.created_at < datetime.now(timezone.utc)

    await asyncio.sleep(0)
    expected_context = Context(session_id=result.id, agent_id=agent.id)
    args, _ = MockAgentRunner.run.call_args
    assert args[0] == expected_context


async def test_create_session_agent_not_found_failure(
    user: User, agent_store: AgentStore, session_service: SessionService
) -> None:
    router = APIRouter()
    create_session_route = mount_create_session_route(router, user, agent_store, session_service)
    params = SessionCreationParamsDTO(agent_id=AgentId(gen_id()), title="Test session")
    with pytest.raises(HTTPException) as exc_info:
        await create_session_route(params, False)
    assert exc_info.value.status_code == 400


async def test_get_session_success(
    user: User, session: Session, session_store: SessionStore
) -> None:
    session = await session_store.create_session(user_id=session.user_id, agent_id=session.agent_id)
    router = APIRouter()

    get_session_route = mount_get_session_route(router, user, session_store)
    rs = await get_session_route(session.id)

    session_dict = asdict(session)
    session_dict.pop("mode")
    assert rs.model_dump() == session_dict


async def test_get_session_not_found_failure(user: User, session_store: SessionStore) -> None:
    router = APIRouter()

    get_session_route = mount_get_session_route(router, user, session_store)
    with pytest.raises(HTTPException) as exc_info:
        await get_session_route(SessionId(gen_id()))
    assert exc_info.value.status_code == 404


async def consume_streaming_response(response: StreamingResponse) -> List[Dict[str, Any]]:
    """Consumes a StreamingResponse and extracts JSON events from an SSE stream.

    Args:
        response (StreamingResponse): The FastAPI streaming response.

    Returns:
        List[Dict[str, Any]]: A list of parsed JSON events.
    """
    events: List[Dict[str, Any]] = []

    async for chunk in response.body_iterator:
        # Convert memoryview -> bytes -> string
        if isinstance(chunk, memoryview):
            chunk = chunk.tobytes().decode()
        elif isinstance(chunk, bytes):
            chunk = chunk.decode()
        elif not isinstance(chunk, str):
            continue  # Skip unexpected chunk types

        # Ensure chunk is a string before processing
        for line in chunk.split("\n\n"):  # SSE messages are separated by double newlines
            if line.startswith("data: "):
                json_data = line[6:].strip()  # Remove "data: " prefix
                try:
                    event = json.loads(json_data)  # Parse JSON
                    events.append(event)  # Store parsed event
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, data: {json_data}")  # Debugging
    return events


async def test_create_event_and_stream_success(
    correlator: ContextualCorrelator,
    user: User,
    agent: Agent,
    session: Session,
    session_store: SessionStore,
    session_service: SessionService,
    user_store: UserStore,
    agent_store: AgentStore,
    event_emitter: EventEmitter,
) -> None:
    agent = await agent_store.create_agent(name=agent.name, type=agent.type)
    session = await session_store.create_session(user_id=session.user_id, agent_id=agent.id)

    class MockAgentRunner(AgentRunner):
        async def run(self, context: Context, event_emitter: EventEmitter) -> bool:
            await event_emitter.enqueue_status_event(
                correlation_id=correlator.correlation_id,
                data=StatusEventData(type="status", status="typing"),
            )
            await event_emitter.enqueue_status_event(
                correlation_id=correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
            return True

    session_service._agent_runner_factory = MockAgentRunnerFactory(runner_class=MockAgentRunner)

    router = APIRouter()
    create_event_and_stream_route = mount_create_event_and_stream_route(
        router, user, session_store, session_service, user_store, agent_store, event_emitter
    )
    params = EventCreationParamsDTO(
        type=EventTypeDTO.MESSAGE, source=EventSourceDTO.USER, content="What's the weather in SF?"
    )
    response = await create_event_and_stream_route(session.id, params)
    assert response.status_code == 200
    assert isinstance(response, StreamingResponse)
    events = await consume_streaming_response(response)
    # Assertions
    assert len(events) == 1
    e1 = events[0]
    assert e1["source"] == "ai_agent"
    assert e1["correlation_id"].startswith(correlator.correlation_id)
    assert e1["data"]["status"] == "typing"


async def test_list_session_events_success(
    correlator: ContextualCorrelator, user: User, session: Session, session_store: SessionStore
) -> None:
    router = APIRouter()
    session = await session_store.create_session(user_id=session.user_id, agent_id=session.agent_id)
    await session_store.create_event(
        session_id=session.id,
        source="user",
        type="message",
        correlation_id=correlator.correlation_id,
        data=MessageEventData(
            type="message",
            parts=[ContentPart(type="content", content="Hello World!")],
            participant=Participant(id=user.id, name=user.name),
        ),
    )
    list_session_events_route = mount_list_session_events_route(router, user, session_store)
    response = await list_session_events_route(session.id, None, None, None, None)
    events = response.data
    assert len(events) == 1
    e1 = events[0]
    assert e1.id is not None
    assert (
        e1.model_dump()
        == EventDTO(
            id=EventId(e1.id),
            correlation_id=correlator.correlation_id,
            type=EventTypeDTO.MESSAGE,
            source=EventSourceDTO.USER,
            deleted=False,
            offset=0,
            data=MessageEventDataDTO(
                type="message",
                parts=[ContentPartDTO(type="content", content="Hello World!")],
                participant={"id": user.id, "name": user.name},
            ),
            created_at=e1.created_at,
        ).model_dump()
    )

    # filter by offset
    response = await list_session_events_route(session.id, 1, None, None, None)
    assert response.data == []

    # filter by source
    response = await list_session_events_route(
        session.id, None, EventSourceDTO.AI_AGENT, None, None
    )
    assert response.data == []

    # filter by type
    response = await list_session_events_route(session.id, None, EventSourceDTO.USER, None, None)
    assert len(response.data) == 1

    response = await list_session_events_route(session.id, None, None, "non_existing_corr_id", None)
    assert response.data == []

    # filter by correlation_id
    response = await list_session_events_route(
        session.id, None, None, correlator.correlation_id, None
    )
    assert len(response.data) == 1

    # filter by event types
    response = await list_session_events_route(
        session.id, None, None, "non_existing_corr_id", [EventTypeDTO.TOOL]
    )
    assert response.data == []

    response = await list_session_events_route(
        session.id, None, None, None, [EventTypeDTO.TOOL, EventTypeDTO.MESSAGE]
    )
    assert len(response.data) == 1

    # all correct filters
    response = await list_session_events_route(
        session.id,
        0,
        EventSourceDTO.USER,
        correlator.correlation_id,
        [EventTypeDTO.MESSAGE, EventTypeDTO.TOOL],
    )
    assert len(response.data) == 1
