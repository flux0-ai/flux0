from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, Literal, NewType, Optional, TypedDict, TypeVar, Union

DocumentID = NewType("DocumentID", str)
DocumentVersion = NewType("DocumentVersion", str)


class SortingOrder(Enum):
    ASC = True
    DESC = False


class BaseDocument(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion


TDocument = TypeVar("TDocument", bound=BaseDocument)


# MongoDB-like result structure for insert operations.
@dataclass(frozen=True)
class InsertOneResult:
    acknowledged: bool
    inserted_id: DocumentID  # Mimicking MongoDB’s inserted_id field.


@dataclass(frozen=True)
class UpdateOneResult:
    acknowledged: bool
    matched_count: int
    modified_count: int
    upserted_id: Optional[DocumentID]


# MongoDB-like result structure for delete operations.
@dataclass(frozen=True)
class DeleteResult(Generic[TDocument]):
    acknowledged: bool
    deleted_count: int
    deleted_document: Optional[TDocument]


# Define a type-safe JSON Patch operation
class AddOp(TypedDict):
    op: Literal["add"]
    path: str
    value: Any


class RemoveOp(TypedDict):
    op: Literal["remove"]
    path: str


class ReplaceOp(TypedDict):
    op: Literal["replace"]
    path: str
    value: Any


class MoveOp(TypedDict):
    op: Literal["move"]
    from_: str  # note: using from_ instead of 'from' because it's a keyword
    path: str


class CopyOp(TypedDict):
    op: Literal["copy"]
    from_: str
    path: str


class TestOp(TypedDict):
    op: Literal["test"]
    path: str
    value: Any


# Union type for JSON patch operations.
JSONPatchOperation = Union[AddOp, RemoveOp, ReplaceOp, MoveOp, CopyOp, TestOp]
