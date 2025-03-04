from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends, status
from flux0_core.agents import AgentStore

from flux0_api.auth import AuthedUser
from flux0_api.common import apigen_config, example_json_content
from flux0_api.dependency_injection import get_agent_store
from flux0_api.types_agents import AgentCreationParamsDTO, AgentDTO, agent_example

API_GROUP = "agents"


def mount_create_agent_route(
    router: APIRouter,
) -> Callable[
    [AuthedUser, AgentCreationParamsDTO, AgentStore],
    Coroutine[Any, Any, AgentDTO],
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
    async def create_agent_route(
        authedUser: AuthedUser,
        params: AgentCreationParamsDTO,
        agent_store: AgentStore = Depends(get_agent_store),
    ) -> AgentDTO:
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

    return create_agent_route
