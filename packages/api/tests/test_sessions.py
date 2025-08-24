import asyncio
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from flux0_api.session_service import SessionService
from flux0_api.sessions import (
    mount_create_event_and_stream_route,
    mount_create_session_route,
    mount_list_session_events_route,
    mount_retrieve_session_route,
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
from flux0_core.agent_runners.api import AgentRunner, Deps
from flux0_core.agent_runners.context import Context
from flux0_core.agents import Agent, AgentId, AgentStore
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id
from flux0_core.recordings import RecordingId, RecordingStore
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
from flux0_stream.types import ChunkEvent

from .conftest import MockAgentRunnerFactory


async def test_create_session_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    session_service: SessionService,
    recording_store: RecordingStore,
) -> None:
    agent = await agent_store.create_agent(
        name=agent.name, type=agent.type, description=agent.description
    )

    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_session_route = mount_create_session_route(router)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session")
    response = Response()
    result: SessionDTO = await create_session_route(
        user, response, params, agent_store, session_service, recording_store, False
    )

    # Assert the returned session has expected values.
    assert result.id is not None
    assert result.agent_id == agent.id
    # assert result.user_id == "user123"
    assert result.title == "Test session"
    # Check that the consumption_offsets is set correctly.
    assert result.consumption_offsets.client == 0

    assert result.created_at < datetime.now(timezone.utc)


async def test_create_session_with_greeting_success(
    correlator: ContextualCorrelator,
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    recording_store: RecordingStore,
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
    create_session_route = mount_create_session_route(router)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session")
    response = Response()
    result: SessionDTO = await create_session_route(
        user, response, params, agent_store, session_service, recording_store, True
    )

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
    user: User,
    agent_store: AgentStore,
    session_service: SessionService,
    recording_store: RecordingStore,
) -> None:
    router = APIRouter()
    create_session_route = mount_create_session_route(router)
    params = SessionCreationParamsDTO(agent_id=AgentId(gen_id()), title="Test session")

    response = Response()
    with pytest.raises(HTTPException) as exc_info:
        await create_session_route(
            user, response, params, agent_store, session_service, recording_store, False
        )
    assert exc_info.value.status_code == 400


async def test_get_session_success(
    user: User, session: Session, session_store: SessionStore
) -> None:
    session = await session_store.create_session(user_id=session.user_id, agent_id=session.agent_id)
    router = APIRouter()

    get_session_route = mount_retrieve_session_route(router)
    rs = await get_session_route(user, session.id, session_store)

    session_dict = asdict(session)
    assert rs.model_dump() == session_dict


async def test_get_session_not_found_failure(user: User, session_store: SessionStore) -> None:
    router = APIRouter()

    get_session_route = mount_retrieve_session_route(router)
    with pytest.raises(HTTPException) as exc_info:
        await get_session_route(user, SessionId(gen_id()), session_store)
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

            # Process each SSE event block
        event_data = ""
        for line in chunk.split("\n"):
            line = line.strip()

            if line.startswith("data: "):  # Extract only JSON data
                event_data = line[6:].strip()  # Remove "data: " prefix

                try:
                    parsed_json = json.loads(event_data)  # Parse JSON
                    events.append(parsed_json)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, data: {event_data}")  # Debugging

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
    recording_store: RecordingStore,
    event_emitter: EventEmitter,
) -> None:
    agent = await agent_store.create_agent(name=agent.name, type=agent.type)
    session = await session_store.create_session(user_id=session.user_id, agent_id=agent.id)

    class MockAgentRunner(AgentRunner):
        async def run(self, context: Context, deps: Deps) -> bool:
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="typing"),
            )
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
            return True

    session_service._agent_runner_factory = MockAgentRunnerFactory(runner_class=MockAgentRunner)

    router = APIRouter()
    create_event_and_stream_route = mount_create_event_and_stream_route(router)
    params = EventCreationParamsDTO(
        type=EventTypeDTO.MESSAGE, source=EventSourceDTO.USER, content="What's the weather in SF?"
    )
    response = await create_event_and_stream_route(
        user,
        session.id,
        params,
        session_service,
        session_store,
        user_store,
        agent_store,
        recording_store,
        event_emitter,
    )
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
    list_session_events_route = mount_list_session_events_route(router)
    response = await list_session_events_route(
        user, session.id, session_store, None, None, None, None
    )
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
    response = await list_session_events_route(user, session.id, session_store, 1, None, None, None)
    assert response.data == []

    # filter by source
    response = await list_session_events_route(
        user, session.id, session_store, None, EventSourceDTO.AI_AGENT, None, None
    )
    assert response.data == []

    # filter by type
    response = await list_session_events_route(
        user, session.id, session_store, None, EventSourceDTO.USER, None, None
    )
    assert len(response.data) == 1

    response = await list_session_events_route(
        user, session.id, session_store, None, None, "non_existing_corr_id", None
    )
    assert response.data == []

    # filter by correlation_id
    response = await list_session_events_route(
        user, session.id, session_store, None, None, correlator.correlation_id, None
    )
    assert len(response.data) == 1

    # filter by event types
    response = await list_session_events_route(
        user, session.id, session_store, None, None, "non_existing_corr_id", [EventTypeDTO.TOOL]
    )
    assert response.data == []

    response = await list_session_events_route(
        user, session.id, session_store, None, None, None, [EventTypeDTO.TOOL, EventTypeDTO.MESSAGE]
    )
    assert len(response.data) == 1

    # all correct filters
    response = await list_session_events_route(
        user,
        session.id,
        session_store,
        0,
        EventSourceDTO.USER,
        correlator.correlation_id,
        [EventTypeDTO.MESSAGE, EventTypeDTO.TOOL],
    )
    assert len(response.data) == 1


#################
# recording tests
#################


async def test_create_session_no_recording(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    session_service: SessionService,
    recording_store: RecordingStore,
) -> None:
    agent = await agent_store.create_agent(
        name=agent.name, type=agent.type, description=agent.description
    )

    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_session_route = mount_create_session_route(router)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session")
    response = Response()
    result: SessionDTO = await create_session_route(
        user, response, params, agent_store, session_service, recording_store, False
    )

    # should not record
    rec1_by_sessid = await recording_store.read_header_by_source_session_id(result.id)
    assert rec1_by_sessid is None


async def test_create_session_recording_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
    session_service: SessionService,
    recording_store: RecordingStore,
) -> None:
    agent = await agent_store.create_agent(
        name=agent.name, type=agent.type, description=agent.description
    )

    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_session_route = mount_create_session_route(router)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = SessionCreationParamsDTO(agent_id=agent.id, title="Test session", mode="record")
    response = Response()
    session = await create_session_route(
        user, response, params, agent_store, session_service, recording_store, False
    )
    assert session.metadata is not None
    recording_id = session.metadata["recording"]["recording_id"]
    rec1_by_recid = await recording_store.read_header_by_recording_id(RecordingId(recording_id))
    rec1_by_sessid = await recording_store.read_header_by_source_session_id(session.id)
    assert rec1_by_sessid == rec1_by_recid


async def test_recorded_events_are_persisted_during_stream(
    correlator: ContextualCorrelator,
    user: User,
    agent: Agent,
    session: Session,
    session_store: SessionStore,
    session_service: SessionService,
    user_store: UserStore,
    agent_store: AgentStore,
    recording_store: RecordingStore,
    event_emitter: EventEmitter,
) -> None:
    # Prepare an agent and create a **recording** session via the API route
    agent = await agent_store.create_agent(name=agent.name, type=agent.type)

    class MockAgentRunner(AgentRunner):
        async def run(self, context: Context, deps: Deps) -> bool:
            # Emit a status, a couple of chunks, then complete
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="typing"),
            )

            eid = EventId("evt-1")
            chunk1 = ChunkEvent(
                correlation_id=deps.correlator.correlation_id,
                event_id=eid,
                seq=0,
                patches=[{"op": "add", "path": "/-", "value": "hello"}],
                metadata={"agent_id": "A1", "agent_name": "STATIC"},
                timestamp=time.time(),
            )
            await deps.event_emitter.enqueue_event_chunk(chunk1)

            # second chunk for same logical stream
            chunk2 = ChunkEvent(
                correlation_id=deps.correlator.correlation_id,
                event_id=eid,
                seq=1,
                patches=[{"op": "add", "path": "/-", "value": " world"}],
                metadata={"agent_id": "A1", "agent_name": "STATIC"},
                timestamp=time.time(),
            )
            await deps.event_emitter.enqueue_event_chunk(chunk2)

            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
            return True

    # Inject the mock runner
    from .conftest import MockAgentRunnerFactory

    session_service._agent_runner_factory = MockAgentRunnerFactory(runner_class=MockAgentRunner)

    router = APIRouter()
    create_session_route = mount_create_session_route(router)
    create_event_and_stream_route = mount_create_event_and_stream_route(router)

    # Create the session in record mode (capture returned session so we stream into the same one)
    params = SessionCreationParamsDTO(agent_id=agent.id, title="rec-test", mode="record")
    resp = Response()
    created = await create_session_route(
        user, resp, params, agent_store, session_service, recording_store, False
    )

    # Kick off a user message that triggers the stream for THIS recorded session
    ev_params = EventCreationParamsDTO(
        type=EventTypeDTO.MESSAGE,
        source=EventSourceDTO.USER,
        content="ping",
    )
    response = await create_event_and_stream_route(
        user,
        created.id,
        ev_params,
        session_service,
        session_store,
        user_store,
        agent_store,
        recording_store,
        event_emitter,
    )

    assert response.status_code == 200
    assert isinstance(response, StreamingResponse)
    # Consume the stream to completion so events are emitted/recorded
    _ = await consume_streaming_response(response)

    # Lookup the recording header for this session to get its recording_id
    header = await recording_store.read_header_by_source_session_id(created.id)
    assert header is not None

    # Fetch recorded frames after the header; ensure statuses and chunks were captured
    frames = await recording_store.read_frames_range(
        recording_id=header.recording_id,
        start_offset_inclusive=1,
        end_offset_exclusive=None,
    )
    assert len(frames) >= 3  # at least typing, two chunks, completed

    kinds = [f.kind for f in frames]
    assert "chunk" in kinds
    assert kinds.count("chunk") == 2

    emitted_statuses = [
        f
        for f in frames
        if f.kind == "emitted" and isinstance(f.payload, dict) and f.payload.get("type") == "status"
    ]
    assert len(emitted_statuses) >= 1
