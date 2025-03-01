from dataclasses import dataclass
from typing import Generic, NewType, Optional, Protocol, TypeVar

DocumentID = NewType("DocumentID", str)
DocumentVersion = NewType("DocumentVersion", str)


class Document(Protocol):
    id: DocumentID
    version: DocumentVersion


# Type variable bound to Document to ensure type safety.
TDocument = TypeVar("TDocument", bound=Document)


# MongoDB-like result structure for insert operations.
@dataclass(frozen=True)
class InsertOneResult:
    acknowledged: bool
    inserted_id: DocumentID  # Mimicking MongoDB’s inserted_id field.


# MongoDB-like result structure for delete operations.
@dataclass(frozen=True)
class DeleteResult(Generic[TDocument]):
    acknowledged: bool
    deleted_count: int
    deleted_document: Optional[TDocument]
