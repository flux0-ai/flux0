from dataclasses import asdict
from datetime import datetime, timezone

import pytest
from fastapi import APIRouter, HTTPException
from flux0_api.agents import (
    mount_create_agent_route,
    mount_list_agents_route,
    mount_retrieve_agent_route,
)
from flux0_api.types_agents import AgentCreationParamsDTO, AgentDTO
from flux0_core.agents import Agent, AgentId, AgentStore
from flux0_core.ids import gen_id
from flux0_core.users import User


async def test_create_agent_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
) -> None:
    router = APIRouter()

    # Mount the route and get the inner function to test.
    create_route = mount_create_agent_route(router)

    # Create a dummy agent creation DTO. Adjust fields as needed.
    params = AgentCreationParamsDTO(name=agent.name, type=agent.type, description=agent.description)
    result: AgentDTO = await create_route(user, params, agent_store)

    # Assert the returned agent has expected values.
    assert result.model_dump(exclude={"id", "created_at"}) == {
        "name": agent.name,
        "type": agent.type,
        "description": agent.description,
    }
    assert result.created_at < datetime.now(timezone.utc)


async def test_read_agent_success(
    user: User,
    agent: Agent,
    agent_store: AgentStore,
) -> None:
    agent = await agent_store.create_agent(agent.name, agent.type, agent.description)
    router = APIRouter()

    read_route = mount_retrieve_agent_route(router)
    rs = await read_route(user, agent.id, agent_store)

    agent_dict = asdict(agent)
    assert rs.model_dump() == agent_dict


async def test_read_agent_not_found_failure(user: User, agent_store: AgentStore) -> None:
    router = APIRouter()

    read_route = mount_retrieve_agent_route(router)
    with pytest.raises(HTTPException) as exc_info:
        await read_route(user, AgentId(gen_id()), agent_store)
    assert exc_info.value.status_code == 404


async def test_list_agents_success(user: User, agent: Agent, agent_store: AgentStore) -> None:
    agent = await agent_store.create_agent(agent.name, agent.type, agent.description)
    router = APIRouter()

    list_route = mount_list_agents_route(router)
    rs = await list_route(user, agent_store)

    agent_dict = asdict(agent)
    assert rs.model_dump()["data"] == [agent_dict]
