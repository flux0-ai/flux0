from datetime import datetime, timezone

from fastapi import APIRouter
from flux0_api.agents import (
    mount_create_agent_route,
)
from flux0_api.types_agents import AgentCreationParamsDTO, AgentDTO
from flux0_core.agents import Agent, AgentStore
from flux0_core.users import User


async def test_create_session_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
) -> None:
    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_route = mount_create_agent_route(router)

    # Create a dummy session creation DTO. Adjust fields as needed.
    params = AgentCreationParamsDTO(name=agent.name, type=agent.type, description=agent.description)
    result: AgentDTO = await create_route(user, params, agent_store)

    # Assert the returned session has expected values.
    assert result.model_dump(exclude={"id", "created_at"}) == {
        "name": agent.name,
        "type": agent.type,
        "description": agent.description,
    }
    assert result.created_at < datetime.now(timezone.utc)
