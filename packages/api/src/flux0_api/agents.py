from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends, HTTPException, status
from flux0_core.agents import AgentStore

from flux0_api.auth import AuthedUser
from flux0_api.common import apigen_config, example_json_content
from flux0_api.dependency_injection import get_agent_store, get_session_service
from flux0_api.session_service import SessionService
from flux0_api.types_agents import (
    AgentCreationParamsDTO,
    AgentDTO,
    AgentIdPath,
    AgentsDTO,
    agent_example,
)

API_GROUP = "agents"


def mount_create_agent_route(
    router: APIRouter,
) -> Callable[
    [AuthedUser, AgentCreationParamsDTO, AgentStore, SessionService], Coroutine[None, Any, AgentDTO]
]:
    @router.post(
        "",
        tags=[API_GROUP],
        operation_id="create_agent",
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Agent created successfully, Returns the created agent along with its generated ID.",
                "content": example_json_content(agent_example),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error in request parameters"
            },
        },
        response_model=AgentDTO,
        response_model_exclude_none=True,
        **apigen_config(group_name=API_GROUP, method_name="create"),
    )
    async def create_agent(
        authedUser: AuthedUser,
        params: AgentCreationParamsDTO,
        agent_store: AgentStore = Depends(get_agent_store),
        session_service: SessionService = Depends(get_session_service),
    ) -> AgentDTO:
        """Creates a new agent with the specified parameters."""

        # Ensure the agent type is supported by the agent runner factory.
        if not session_service._agent_runner_factory.runner_exists(params.type):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Agent type '{params.type}' is not supported",
            )

        agent = await agent_store.create_agent(
            name=params and params.name or "Unnamed Agent",
            type=params.type,
            description=params and params.description or None,
        )

        return AgentDTO(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            created_at=agent.created_at,
        )

    return create_agent


def mount_retrieve_agent_route(
    router: APIRouter,
) -> Callable[[AuthedUser, AgentIdPath, AgentStore], Coroutine[Any, Any, AgentDTO]]:
    @router.get(
        "/{agent_id}",
        tags=[API_GROUP],
        operation_id="retrieve_agent",
        response_model=AgentDTO,
        responses={
            status.HTTP_200_OK: {
                "description": "Agent details successfully retrieved. Returns the complete agent object.",
                "content": example_json_content(agent_example),
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Agent not found. The specified `agent_id` does not exist"
            },
        },
        **apigen_config(group_name=API_GROUP, method_name="retrieve"),
    )
    async def retrieve_agent(
        _: AuthedUser,
        agent_id: AgentIdPath,
        agent_store: AgentStore = Depends(get_agent_store),
    ) -> AgentDTO:
        """
        Retrieves details of a specific agent by ID.
        """
        agent = await agent_store.read_agent(agent_id=agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found",
            )

        return AgentDTO(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            created_at=agent.created_at,
        )

    return retrieve_agent


def mount_list_agents_route(
    router: APIRouter,
) -> Callable[[AuthedUser, AgentStore], Coroutine[Any, Any, AgentsDTO]]:
    @router.get(
        "",
        tags=[API_GROUP],
        operation_id="list_agents",
        response_model=AgentsDTO,
        responses={
            status.HTTP_200_OK: {
                "description": "List of all agents in the system",
                "content": example_json_content({"data": [agent_example]}),
            }
        },
        **apigen_config(group_name=API_GROUP, method_name="list"),
    )
    async def list_agents(
        _: AuthedUser,
        agent_store: AgentStore = Depends(get_agent_store),
    ) -> AgentsDTO:
        """
        Retrieves a list of all agents in the system.

        Returns an empty list if no agents exist.
        Agents are returned in no guaranteed order.
        """
        agents = await agent_store.list_agents()
        return AgentsDTO(
            data=[
                AgentDTO(
                    id=a.id,
                    name=a.name,
                    type=a.type,
                    description=a.description,
                    created_at=a.created_at,
                )
                for a in agents
            ]
        )

    return list_agents
