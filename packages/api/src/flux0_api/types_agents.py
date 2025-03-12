from datetime import datetime
from typing import Annotated, Optional, Sequence, TypeAlias

import dateutil
import dateutil.parser
from fastapi import Path, Query
from flux0_core.agents import AgentId, AgentType
from pydantic import Field

from flux0_api.common import DEFAULT_MODEL_CONFIG, DefaultBaseModel, ExampleJson

agent_id_example = "vUfk4PgjTm"
agent_name_examples = ["Drizzle", "Smarty"]
agent_title_example = "What's the weather in SF?"
agent_type_example = "weather"
agent_description_example = "An agent that checks the weather"

agent_example: ExampleJson = {
    "id": agent_id_example,
    "name": agent_name_examples[0],
    "type": agent_type_example,
    "description": agent_description_example,
    "creation_utc": "2025-01-21T23:44:48",
}


AgentIdPath: TypeAlias = Annotated[
    AgentId,
    Path(
        description="Unique identifier for the agent",
        examples=[agent_id_example],
        min_length=10,
        max_length=10,
    ),
]


AgentNameField: TypeAlias = Annotated[
    str,
    Field(
        description="The display name of the agent, mainly for representation purposes",
        examples=agent_name_examples,
        min_length=1,
        max_length=100,
    ),
]

AgentTypeField: TypeAlias = Annotated[
    AgentType,
    Field(
        description="The type of the agent",
        examples=[agent_type_example],
        min_length=1,
        max_length=100,
    ),
]

AgentDescriptionField: TypeAlias = Annotated[
    str,
    Field(
        default=None,
        description="Detailed of the agent's purpose and capabilities",
        examples=[agent_description_example],
    ),
]

AgentCreatedField: TypeAlias = Annotated[
    datetime,
    Field(
        description="When the agent was created",
        examples=[dateutil.parser.parse("2025-01-21T23:44:48")],
    ),
]


class AgentDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": agent_example,
    }

    """
    An agent is a specialized AI persona crafted for a specific service role.
    """

    id: AgentIdPath
    name: AgentNameField
    type: AgentTypeField
    description: Optional[AgentDescriptionField] = None
    created_at: AgentCreatedField


# ===========================
# Create Agent
# ===========================

agent_creation_params_example: ExampleJson = {
    "name": agent_name_examples[0],
    "type": agent_type_example,
    "description": agent_description_example,
}


class AgentCreationParamsDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": agent_creation_params_example,
    }

    """
    Parameters for creating a new agent.
    """

    name: AgentNameField
    type: AgentTypeField
    description: Optional[AgentDescriptionField] = None


# ===========================
# List Agents
# ===========================
class AgentsDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "data": [agent_example],
        }
    }

    """
    List of agents in the system.
    """
    data: Sequence[AgentDTO]


# ===========================
# Misc
# ===========================

AgentIdQuery: TypeAlias = Annotated[
    AgentId,
    Query(
        description="Unique identifier of the agent",
        examples=["t5ul4jGZjb"],
    ),
]
