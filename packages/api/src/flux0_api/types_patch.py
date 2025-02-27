from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from flux0_api.common import DefaultBaseModel, JSONSerializableDTO

PatchOpOpField: TypeAlias = Annotated[
    Literal["add", "replace"],
    Field(
        description="The operation to perform",
        examples=["add", "replace"],
    ),
]

PatchOpPathField: TypeAlias = Annotated[
    str,
    Field(
        description="The path to the target",
        examples=["/-", "/foo"],
    ),
]


class JsonPatchOperationDTO(
    DefaultBaseModel,
    json_schema_extra={
        "example": {
            "op": "add",
            "path": "/a/b",
            "value": 1,
        }
    },
):
    op: PatchOpOpField
    path: PatchOpPathField
    value: JSONSerializableDTO
