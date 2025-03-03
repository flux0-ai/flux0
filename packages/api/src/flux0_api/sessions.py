from typing import Any, Callable, Coroutine

from fastapi import APIRouter, HTTPException, status
from flux0_core.agents import AgentStore
from flux0_core.sessions import SessionStore

from flux0_api.auth import AuthedUser
from flux0_api.common import apigen_config, example_json_content
from flux0_api.session_service import SessionService
from flux0_api.types_session import (
    AllowGreetingQuery,
    ConsumptionOffsetsDTO,
    SessionCreationParamsDTO,
    SessionDTO,
    SessionIdPath,
    session_example,
)

API_GROUP = "sessions"


def mount_create_session_route(
    router: APIRouter,
    authedUser: AuthedUser,
    agent_store: AgentStore,
    session_service: SessionService,
) -> Callable[[SessionCreationParamsDTO, AllowGreetingQuery], Coroutine[Any, Any, SessionDTO]]:
    @router.post(
        "",
        tags=[API_GROUP],
        summary="Create a new session",
        response_model=SessionDTO,
        status_code=201,
        response_model_exclude_none=True,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Session created successfully, Returns the created session along with its generated ID.",
                "content": example_json_content(session_example),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error in request parameters"
            },
        },
        **apigen_config(group_name=API_GROUP, method_name="create"),
    )
    async def create_session_route(
        params: SessionCreationParamsDTO, allow_greeting: AllowGreetingQuery = False
    ) -> SessionDTO:
        """
        Create a new session bettween a user and an agent.

        The session will be associated with the provided agent and optionally with a user.
        If no user is provided, a guest user will be created.
        """
        agent = await agent_store.read_agent(params.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with ID {params.agent_id} not found",
            )

        session = await session_service.create_user_session(
            id=params.id,
            user_id=authedUser.id,
            agent=agent,
            title=params.title,
            allow_greeting=allow_greeting,
        )

        return SessionDTO(
            id=session.id,
            agent_id=session.agent_id,
            user_id=session.user_id,
            title=session.title,
            consumption_offsets=ConsumptionOffsetsDTO(client=session.consumption_offsets["client"]),
            created_at=session.created_at,
        )

    return create_session_route


def mount_get_session_route(
    router: APIRouter,
    authedUser: AuthedUser,
    session_store: SessionStore,
) -> Callable[[SessionIdPath], Coroutine[Any, Any, SessionDTO]]:
    @router.get(
        "/{session_id}",
        operation_id="read_session",
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
    async def read_session(
        session_id: SessionIdPath,
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
            title=session.title,
            consumption_offsets=ConsumptionOffsetsDTO(
                client=session.consumption_offsets["client"],
            ),
            created_at=session.created_at,
        )

    return read_session
