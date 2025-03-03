from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, Sequence, TypeAlias

import dateutil.parser
from fastapi import Path, Query
from flux0_core.agents import AgentId
from flux0_core.sessions import SessionId
from flux0_core.users import UserId
from pydantic import Field

from flux0_api.common import DEFAULT_MODEL_CONFIG, DefaultBaseModel, ExampleJson
from flux0_api.types_agents import agent_id_example, agent_title_example
from flux0_api.types_users import user_id_example

session_id_example = "zv3h4j5Fjv"
SessionIdPath: TypeAlias = Annotated[
    SessionId,
    Path(
        description="Unique identifier of the session",
        examples=[session_id_example],
        min_length=10,
        max_length=10,
    ),
]


SessionAgentIdPath: TypeAlias = Annotated[
    AgentId,
    Path(
        description="Unique identifier of the agent associated with the session.",
        examples=[agent_id_example],
        min_length=10,
        max_length=10,
    ),
]

SessionUserIdField: TypeAlias = Annotated[
    UserId,
    Field(
        description="Unique identifier of the user associated with the session.",
        examples=[user_id_example],
        min_length=10,
        max_length=10,
    ),
]

SessionCreatedField: TypeAlias = Annotated[
    datetime,
    Field(
        description="When the session was created",
        examples=[dateutil.parser.parse("2025-01-25T22:41:41")],
    ),
]

SessionTitleField: TypeAlias = Annotated[
    str,
    Field(
        description="Descriptive title of the session",
        examples=["A tale about a friendly dragon and a lost princess"],
        max_length=200,
    ),
]

consumption_offsets_example = {"client": 37}

ConsumptionOffsetClientField: TypeAlias = Annotated[
    int,
    Field(
        description="The most recent event offset processed by the client",
        examples=[37, 100],
        ge=0,
    ),
]


class ConsumptionOffsetsDTO(
    DefaultBaseModel,
    json_schema_extra={"example": consumption_offsets_example},
):
    """Tracks the state of message consumption."""

    client: Optional[ConsumptionOffsetClientField] = None


session_title_example = "The weather in SF"

session_example: ExampleJson = {
    "id": session_id_example,
    "agent_id": agent_id_example,
    "user_id": user_id_example,
    "title": session_title_example,
    "created_at": "2025-01-29T09:27:41Z",
}


class SessionDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": session_example,
    }

    """
    A session represents an on going interaction between a user and an agent.
    """

    id: SessionIdPath
    agent_id: SessionAgentIdPath
    user_id: SessionUserIdField
    title: Optional[SessionTitleField] = None
    consumption_offsets: ConsumptionOffsetsDTO
    created_at: SessionCreatedField


class SessionsDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {"example": {"data": [session_example]}}

    """
    List of sessions in the system.
    """
    data: Sequence[SessionDTO]


session_creation_params_example: ExampleJson = {
    "agent_id": agent_id_example,
    "title": agent_title_example,
}


class SessionCreationParamsDTO(DefaultBaseModel):
    model_config = DEFAULT_MODEL_CONFIG.copy()
    model_config["json_schema_extra"] = {
        "example": session_creation_params_example,
    }
    """
    Parameters required to create a new session.
    """
    agent_id: SessionAgentIdPath
    id: Optional[SessionIdPath] = None
    title: Optional[SessionTitleField] = None


AllowGreetingQuery: TypeAlias = Annotated[
    bool,
    Query(
        description="Indicates if the agent is permitted to send an initial greeting",
    ),
]


class Moderation(Enum):
    """Content moderation settings."""

    # AUTO = "auto"
    NONE = "none"


ModerationQuery: TypeAlias = Annotated[
    Moderation,
    Query(
        description="Content moderation level for the event",
    ),
]
