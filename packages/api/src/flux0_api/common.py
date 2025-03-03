from typing import Annotated, Any, Mapping, TypeAlias, cast

from fastapi import Request
from lagom import Container
from pydantic import BaseModel, ConfigDict, Field

#: `ExampleJson` represents a JSON structure, either:
#: - A dictionary with string keys and any values
#: - A list of any values
#:
#: Used to define example JSON payloads for OpenAPI docs.
ExampleJson: TypeAlias = dict[str, Any] | list[Any]

#: `ExtraSchema` defines an OpenAPI-compatible schema for example JSON content.
#:
#: It maps a MIME type (e.g., `"application/json"`) to a dictionary
#: containing OpenAPI keys like `"example"`, holding the JSON data.
#:
#: Used in `example_json_content()` to generate OpenAPI examples.
ExtraSchema: TypeAlias = dict[str, dict[str, Any]]


JSONSerializableDTO: TypeAlias = Annotated[
    Any,
    Field(
        description="Any valid JSON",
        examples=['"foo"', "[1, 2]", '{"data"="bar", "data2"="baz"}'],
    ),
]


def example_json_content(json_example: ExampleJson) -> ExtraSchema:
    """Creates an OpenAPI-compatible example JSON content schema.

    Args:
        json_example (ExampleJson): The example JSON data to include in the schema.

    Returns:
        ExtraSchema: A dictionary structured for OpenAPI documentation,
                     mapping "application/json" to an example payload.
    """
    return {"application/json": {"example": json_example}}


def _strip_dto_suffix(obj: Any, *args: Any) -> str:
    if isinstance(obj, str):
        name = obj
        if name.endswith("DTO"):
            return name[:-3]
        return name
    if isinstance(obj, type):
        name = obj.__name__
        if name.endswith("DTO"):
            return name[:-3]
        return name
    else:
        raise Exception("Invalid type for _strip_dto_suffix")


DEFAULT_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    validate_default=True,
    model_title_generator=_strip_dto_suffix,
)


class DefaultBaseModel(BaseModel):
    """
    Base class for all WeTale Pydantic models.
    """

    model_config = DEFAULT_MODEL_CONFIG


def apigen_config(group_name: str, method_name: str) -> Mapping[str, Any]:
    """Instruct Fern to generate correct SDK method names.
    https://buildwithfern.com/learn/api-definition/openapi/frameworks/fastapi
    ."""
    return {
        "openapi_extra": {
            "x-fern-sdk-group-name": group_name,
            "x-fern-sdk-method-name": method_name,
        }
    }


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)
