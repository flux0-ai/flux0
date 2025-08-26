import asyncio
import json
from datetime import datetime, timezone
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from flux0_core.agents import AgentStore
from flux0_core.ids import gen_id
from flux0_core.recordings import (
    RecordedChunkPayload,
    RecordedEmittedPayload,
    RecordedEvent,
    RecordingStore,
)
from flux0_core.sessions import (
    ContentPart,
    Event,
    EventType,
    MessageEventData,
    SessionId,
    SessionStore,
    StatusEventData,
    ToolEventData,
)
from flux0_core.users import UserStore
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.types import ChunkEvent, EmittedEvent

from flux0_api.auth import AuthedUser
from flux0_api.common import JSONSerializableDTO, apigen_config, example_json_content
from flux0_api.dependency_injection import (
    get_agent_store,
    get_event_emitter,
    get_recording_store,
    get_session_service,
    get_session_store,
    get_user_store,
)
from flux0_api.session_service import SessionService
from flux0_api.types_agents import AgentIdQuery
from flux0_api.types_events import (
    CorrelationIdQuery,
    EventCreationParamsDTO,
    EventDTO,
    EventsDTO,
    EventSourceDTO,
    EventTypeDTO,
    MinOffsetQuery,
    SessionStream,
    TypesQuery,
    emitted_event_chunk_example,
    emitted_status_event_example,
    event_example,
)
from flux0_api.types_session import (
    AllowGreetingQuery,
    ConsumptionOffsetsDTO,
    SessionCreationParamsDTO,
    SessionDTO,
    SessionIdPath,
    SessionsDTO,
    session_example,
)

API_GROUP = "sessions"


def mount_create_session_route(
    router: APIRouter,
) -> Callable[
    [
        AuthedUser,
        Response,
        SessionCreationParamsDTO,
        AgentStore,
        SessionService,
        RecordingStore,
        AllowGreetingQuery,
    ],
    Coroutine[Any, Any, SessionDTO],
]:
    @router.post(
        "",
        tags=[API_GROUP],
        summary="Create Session",
        operation_id="create_session",
        response_model=SessionDTO,
        status_code=201,
        response_model_exclude_none=True,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Session created successfully, Returns the created session along with its generated ID.",
                "content": example_json_content(session_example),
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Invalid request parameters, such as missing agent ID or invalid session ID format."
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error in request parameters"
            },
            status.HTTP_409_CONFLICT: {"description": "Session with the same ID already exists"},
        },
        **apigen_config(group_name=API_GROUP, method_name="create"),
    )
    async def create_session_route(
        authedUser: AuthedUser,
        response: Response,
        params: SessionCreationParamsDTO,
        agent_store: AgentStore = Depends(get_agent_store),
        session_service: SessionService = Depends(get_session_service),
        recording_store: RecordingStore = Depends(get_recording_store),
        allow_greeting: AllowGreetingQuery = False,
    ) -> SessionDTO:
        """
        Create a new session between a user and an agent.

        The session will be associated with the provided agent and optionally with a user.
        If no user is provided, a guest user will be created.
        """
        agent = await agent_store.read_agent(params.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with ID {params.agent_id} not found",
            )

        if not session_service._agent_runner_factory.runner_exists(agent.type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent type {agent.type} is not supported by the server",
            )

        session_id = params.id if params.id else SessionId(gen_id())
        if params.mode == "record":
            recorded_event_header = await recording_store.create_recording(
                source_session_id=session_id,
            )
            if params.metadata is None or not isinstance(params.metadata, dict):
                params.metadata = {}
            params.metadata["recording"] = {"recording_id": str(recorded_event_header.recording_id)}

        session = await session_service.create_user_session(
            id=session_id,
            user_id=authedUser.id,
            agent=agent,
            title=params.title,
            allow_greeting=allow_greeting,
            mode=params.mode,
            metadata=params.metadata,
        )

        return SessionDTO(
            id=session.id,
            agent_id=session.agent_id,
            user_id=session.user_id,
            mode=session.mode,
            title=session.title,
            consumption_offsets=ConsumptionOffsetsDTO(client=session.consumption_offsets["client"]),
            created_at=session.created_at,
            metadata=session.metadata,
        )

    return create_session_route


def mount_retrieve_session_route(
    router: APIRouter,
) -> Callable[[AuthedUser, SessionIdPath, SessionStore], Coroutine[Any, Any, SessionDTO]]:
    @router.get(
        "/{session_id}",
        tags=[API_GROUP],
        operation_id="retrieve_session",
        response_model=SessionDTO,
        response_model_exclude_none=True,
        responses={
            status.HTTP_200_OK: {
                "description": "Session details retrieved successfully",
                "content": {"application/json": {"example": session_example}},
            },
            status.HTTP_404_NOT_FOUND: {"description": "Session not found"},
        },
        **apigen_config(group_name=API_GROUP, method_name="retrieve"),
    )
    async def retrieve_session(
        authedUser: AuthedUser,
        session_id: SessionIdPath,
        session_store: SessionStore = Depends(get_session_store),
    ) -> SessionDTO:
        """Retrieve details of a session by its unique identifier"""

        session = await session_store.read_session(session_id=session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found",
            )

        return SessionDTO(
            id=session.id,
            agent_id=session.agent_id,
            user_id=session.user_id,
            mode=session.mode,
            title=session.title,
            consumption_offsets=ConsumptionOffsetsDTO(
                client=session.consumption_offsets["client"],
            ),
            created_at=session.created_at,
            metadata=session.metadata,
        )

    return retrieve_session


def mount_list_sessions_route(
    router: APIRouter,
) -> Callable[[AuthedUser, Optional[AgentIdQuery], SessionStore], Coroutine[Any, Any, SessionsDTO]]:
    @router.get(
        "",
        tags=[API_GROUP],
        operation_id="list_sessions",
        response_model=SessionsDTO,
        responses={
            status.HTTP_200_OK: {
                "description": "List of all matching sessions",
                "content": {"application/json": {"example": {"data": [session_example]}}},
            }
        },
        **apigen_config(group_name=API_GROUP, method_name="list"),
    )
    async def list_sessions(
        authedUser: AuthedUser,
        agent_id: Optional[AgentIdQuery] = None,
        session_store: SessionStore = Depends(get_session_store),
    ) -> SessionsDTO:
        """
        Retrieve all sessions that match the given filters.

        Filters can be applied using agent_id. If no filters are specified, all sessions will be returned.
        """

        sessions = await session_store.list_sessions(
            user_id=authedUser.id,
            agent_id=agent_id,
        )

        return SessionsDTO(
            data=[
                SessionDTO(
                    id=s.id,
                    agent_id=s.agent_id,
                    title=s.title,
                    user_id=s.user_id,
                    mode=s.mode,
                    consumption_offsets=ConsumptionOffsetsDTO(
                        client=s.consumption_offsets["client"],
                    ),
                    created_at=s.created_at,
                    metadata=s.metadata,
                )
                for s in sessions
            ]
        )

    return list_sessions


# SSE Generator function
async def event_stream(
    session_id: SessionId,
    correlation_id: str,
    session_store: SessionStore,
    session_service: SessionService,
    event_emitter: EventEmitter,
    subscription_ready: asyncio.Event,
    recording_store: RecordingStore,
) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue[Union[ChunkEvent, EmittedEvent]] = asyncio.Queue()

    async def subscriber(chunk_event: ChunkEvent) -> None:
        """Callback for processed events, pushing them to the queue."""
        await queue.put(chunk_event)

    async def subscriber_final(emitted_event: EmittedEvent) -> None:
        """Callback for finalized events, pushing them to the queue."""
        await queue.put(emitted_event)

    # Subscribe to processed event updates
    # print("subscribed to correlation_id", correlation_id)
    event_emitter.subscribe_processed(correlation_id, subscriber)
    event_emitter.subscribe_final(correlation_id, subscriber_final)
    subscription_ready.set()

    recording = await recording_store.read_header_by_source_session_id(session_id)
    recording_id = recording.recording_id if recording else None
    recording_aborted = False

    async def maybe_record_emitted(payload: RecordedEmittedPayload, created_at: datetime) -> None:
        nonlocal recording_aborted
        if not recording_id or recording_aborted:
            return
        try:
            await recording_store.append_emitted(recording_id, payload, created_at=created_at)
        except Exception:
            recording_aborted = True  # stop further attempts

    async def maybe_record_chunk(payload: RecordedChunkPayload, created_at: datetime) -> None:
        nonlocal recording_aborted
        if not recording_id or recording_aborted:
            return
        try:
            await recording_store.append_chunk(recording_id, payload, created_at=created_at)
        except Exception:
            recording_aborted = True

    try:
        while True:
            event = await queue.get()
            event_type = "unknown"
            # if event.kind != "status":
            # continue
            if isinstance(event, EmittedEvent):
                event_type = event.type
                if event.type == "status":
                    ed = cast(StatusEventData, event.data)
                    if ed["status"] == "completed":
                        await maybe_record_emitted(
                            RecordedEmittedPayload(
                                id=event.id,
                                source=event.source,
                                type="status",
                                correlation_id=event.correlation_id,
                                data=ed,
                                metadata=event.metadata or {},
                            ),
                            created_at=datetime.fromtimestamp(event.timestamp, tz=timezone.utc),
                        )
                        break
                    await session_store.create_event(
                        correlation_id=event.correlation_id,
                        session_id=session_id,
                        source=event.source,
                        type=event.type,
                        data=ed,
                        metadata=event.metadata,
                    )
                    await maybe_record_emitted(
                        RecordedEmittedPayload(
                            id=event.id,
                            source=event.source,
                            type="status",
                            correlation_id=event.correlation_id,
                            data=ed,
                            metadata=event.metadata or {},
                        ),
                        created_at=datetime.fromtimestamp(event.timestamp, tz=timezone.utc),
                    )

                    yield f"event: {event_type}\nid: {event.id}\ndata: {json.dumps(event.__dict__)}\n\n"
                elif event.type == "message":
                    event_type = event.type
                    md = cast(MessageEventData, event.data)
                    if not md.get("parts"):
                        continue
                    await session_store.create_event(
                        correlation_id=event.correlation_id,
                        session_id=session_id,
                        source=event.source,
                        type=event.type,
                        data=md,
                        metadata=event.metadata,
                    )
                elif event.type == "tool":
                    event_type = event.type
                    td = cast(ToolEventData, event.data)
                    await session_store.create_event(
                        correlation_id=event.correlation_id,
                        session_id=session_id,
                        source=event.source,
                        type=event.type,
                        data=td,
                        metadata=event.metadata,
                    )
                else:
                    raise ValueError(f"Unknown event type: {event.type}")
            else:
                # this is a chunk event
                event_type = "chunk"
                await maybe_record_chunk(
                    RecordedChunkPayload(
                        correlation_id=event.correlation_id,
                        event_id=event.event_id,
                        seq=event.seq,
                        patches=event.patches,
                        metadata=event.metadata or {},
                    ),
                    created_at=datetime.fromtimestamp(event.timestamp, tz=timezone.utc),
                )
                yield f"event: {event_type}\ndata: {json.dumps(event.__dict__)}\n\n"
    except asyncio.CancelledError:
        await session_service.cancel_processing_session_task(session_id)
        return
    finally:
        # Unsubscribe when client disconnects
        # print("unsubscribed from correlation_id", correlation_id)
        event_emitter.unsubscribe_processed(correlation_id, subscriber)
        event_emitter.unsubscribe_final(correlation_id, subscriber_final)
        # Explicitly send a termination event before closing
        # yield "event: close\ndata: {}\n\n"


def event_to_dto(event: Event) -> EventDTO:
    return EventDTO(
        id=event.id,
        source=EventSourceDTO(event.source),
        type=EventTypeDTO(event.type),
        offset=event.offset,
        correlation_id=event.correlation_id,
        data=cast(JSONSerializableDTO, event.data),
        metadata=event.metadata,
        deleted=event.deleted,
        created_at=event.created_at,
    )


async def _add_user_message(
    session_id: SessionIdPath,
    params: EventCreationParamsDTO,
    user_store: UserStore,
    agent_store: AgentStore,
    session_store: SessionStore,
    session_service: SessionService,
    rec_header: Optional[RecordedEvent],
    recording_store: RecordingStore,
    # moderation: Moderation = Moderation.NONE,
    subscription_ready: asyncio.Event,
) -> EventDTO:
    if not params.content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing 'message' field in event parameters",
        )

    flagged = False
    tags: Set[str] = set()

    # implement moderation in the future (should set flagged and tags)

    session = await session_store.read_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session with ID {session_id} not found",
        )

    agent = await agent_store.read_agent(session.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with ID {session.agent_id} not found",
        )

    user = await user_store.read_user(session.user_id)
    if user:
        user_display_name = user.name
    else:
        user_display_name = session.user_id

    message_data: MessageEventData = {
        "type": "message",
        "participant": {
            "id": session.user_id,
            "name": user_display_name,
        },
        "flagged": flagged,
        "tags": list(tags),
        "parts": [
            ContentPart(
                type="content",
                content=params.content,
            )
        ],
    }

    event = await session_service.post_event(
        session=session,
        agent=agent,
        type=params.type.value,
        data=message_data,
        source="user",
        trigger_processing=True,
        wait_event=subscription_ready,
    )

    if rec_header:
        await recording_store.append_emitted(
            recording_id=rec_header.recording_id,
            payload=RecordedEmittedPayload(
                id=event.id,
                source=event.source,
                type=event.type,
                correlation_id=event.correlation_id,
                data=event.data,
                metadata=event.metadata or {},
            ),
        )

    return event_to_dto(event)


def mount_create_event_and_stream_route(
    router: APIRouter,
) -> Callable[
    [
        AuthedUser,
        SessionIdPath,
        EventCreationParamsDTO,
        SessionService,
        SessionStore,
        UserStore,
        AgentStore,
        RecordingStore,
        EventEmitter,
    ],
    Coroutine[Any, Any, StreamingResponse],
]:
    @router.post(
        "/{session_id}/events/stream",
        tags=[API_GROUP],
        status_code=status.HTTP_200_OK,
        operation_id="create_event_and_stream",
        summary="Create Event and Stream",
        description="Creates a new user event in the specified session and streams upcoming events.",
        response_class=StreamingResponse,
        response_model=SessionStream,
        responses={
            status.HTTP_200_OK: {
                "description": "Server-Sent Events (SSE) stream with structured event types",
                "content": {
                    "text/event-stream": {
                        "schema": {"$ref": "#/components/schemas/SessionStream"},
                        "examples": {
                            "status": {
                                "summary": "Status Event",
                                "value": (
                                    "event: status\n"
                                    + "data: "
                                    + json.dumps(emitted_status_event_example)
                                ),
                            },
                            # "tool": {
                            #     "summary": "Tool Event",
                            #     "value": (
                            #         "event: tool\n"
                            #         + "data: "
                            #         + json.dumps(emitted_tool_event_example)
                            #     ),
                            # },
                            "chunk": {
                                "summary": "Content Event",
                                "value": (
                                    "event: chunk\ndata: " + json.dumps(emitted_event_chunk_example)
                                ),
                            },
                        },
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: {"description": "Session not found"},
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error in event parameters"
            },
        },
        **apigen_config(group_name=API_GROUP, method_name="create_event"),
    )
    async def create_event_and_stream(
        _: AuthedUser,
        session_id: SessionIdPath,
        params: EventCreationParamsDTO,
        session_service: SessionService = Depends(get_session_service),
        session_store: SessionStore = Depends(get_session_store),
        user_store: UserStore = Depends(get_user_store),
        agent_store: AgentStore = Depends(get_agent_store),
        recording_store: RecordingStore = Depends(get_recording_store),
        event_emitter: EventEmitter = Depends(get_event_emitter),
        # moderation: ModerationQuery = Moderation.NONE,
    ) -> StreamingResponse:
        """Creates a new event in the specified session in streaming mode.

        Currently supports creating message events from user and human agent sources."""

        if params.type != EventTypeDTO.MESSAGE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only message events can currently be added manually",
            )

        rec_header = await recording_store.read_header_by_source_session_id(session_id)
        subscription_ready = asyncio.Event()
        if params.source == EventSourceDTO.USER:
            event = await _add_user_message(
                session_id,
                params,
                user_store,
                agent_store,
                session_store,
                session_service,
                rec_header,
                recording_store,
                # moderation,
                subscription_ready,
            )

            return StreamingResponse(
                event_stream(
                    session_id,
                    event.correlation_id,
                    session_store,
                    session_service,
                    event_emitter,
                    subscription_ready,
                    recording_store,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        # elif params.source == EventSourceDTO.AI_AGENT:
        #     return await _add_agent_message(session_id, params)
        # elif params.source == EventSourceDTO.HUMAN_AGENT_ON_BEHALF_OF_AI_AGENT:
        #     return await _add_human_agent_message_on_behalf_of_ai_agent(
        #         session_id, params
        #     )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Only "user" source is supported for direct posting.',
            )

    return create_event_and_stream


def mount_list_session_events_route(
    router: APIRouter,
) -> Callable[
    [
        AuthedUser,
        SessionIdPath,
        SessionStore,
        Optional[MinOffsetQuery],
        Optional[EventSourceDTO],
        Optional[CorrelationIdQuery],
        Optional[TypesQuery],
    ],
    Coroutine[Any, Any, EventsDTO],
]:
    @router.get(
        "/{session_id}/events",
        tags=[API_GROUP],
        operation_id="list_session_events",
        response_model=EventsDTO,
        responses={
            status.HTTP_200_OK: {
                "description": "List of events matching the specified criteria",
                "content": {"application/json": {"example": [event_example]}},
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Session not found",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error in request parameters"
            },
            status.HTTP_504_GATEWAY_TIMEOUT: {
                "description": "Request timeout waiting for new events"
            },
        },
        **apigen_config(group_name=API_GROUP, method_name="list_events"),
    )
    async def list_events(
        user: AuthedUser,
        session_id: SessionIdPath,
        session_store: SessionStore = Depends(get_session_store),
        min_offset: Optional[MinOffsetQuery] = None,
        source: Optional[EventSourceDTO] = None,
        correlation_id: Optional[CorrelationIdQuery] = None,
        types: Optional[TypesQuery] = None,
    ) -> EventsDTO:
        """List events for a session with optional filtering

        Retrieves events that occurred within a session, optionally filtering by source, correlation ID, and types.
        """

        if not await session_store.read_session(session_id=session_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot list events for non-existent session with ID {session_id}",
            )

        type_list: Sequence[EventType] = [t.value for t in types] if types else []

        events = await session_store.list_events(
            session_id=session_id,
            min_offset=min_offset,
            source=source.value if source else None,
            types=type_list,
            correlation_id=correlation_id,
        )

        return EventsDTO(
            data=[
                EventDTO(
                    id=e.id,
                    source=EventSourceDTO(e.source),
                    type=EventTypeDTO(e.type),
                    offset=e.offset,
                    correlation_id=e.correlation_id,
                    data=cast(JSONSerializableDTO, e.data),
                    metadata=e.metadata,
                    deleted=e.deleted,
                    created_at=e.created_at,
                )
                for e in events
            ]
        )

    return list_events
