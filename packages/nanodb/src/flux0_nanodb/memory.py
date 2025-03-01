from dataclasses import asdict, is_dataclass
from typing import Any, Optional, Sequence, Type, cast

from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.query import QueryFilter, matches_query
from flux0_nanodb.types import (
    DeleteResult,
    InsertOneResult,
    TDocument,
)


class MemoryDocumentCollection(DocumentCollection[TDocument]):
    def __init__(self, name: str, schema: Type[TDocument]) -> None:
        self._name = name
        self._schema = schema
        self._documents: list[TDocument] = []

    async def find(self, filters: Optional[QueryFilter] = None) -> Sequence[TDocument]:
        if filters is None:
            return self._documents

        # Convert each document to a dict and evaluate the filter.
        return [
            doc
            for doc in self._documents
            if matches_query(filters, asdict(doc) if is_dataclass(doc) else vars(doc))
        ]

    async def insert_one(self, document: TDocument) -> InsertOneResult:
        self._documents.append(document)
        return InsertOneResult(acknowledged=True, inserted_id=document.id)

    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        for i, doc in enumerate(self._documents):
            if matches_query(filters, asdict(doc) if is_dataclass(doc) else vars(doc)):
                removed = self._documents.pop(i)
                return DeleteResult(acknowledged=True, deleted_count=1, deleted_document=removed)
        return DeleteResult(acknowledged=True, deleted_count=0, deleted_document=None)


class MemoryDocumentDatabase(DocumentDatabase):
    def __init__(self) -> None:
        # We store collections in a dict by name.
        self._collections: dict[str, MemoryDocumentCollection[Any]] = {}

    async def create_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        if name in self._collections:
            raise ValueError(f"Collection '{name}' already exists")
        collection: MemoryDocumentCollection[TDocument] = MemoryDocumentCollection(name, schema)
        self._collections[name] = collection
        return collection

    async def get_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        collection = self._collections.get(name)
        if collection is None:
            raise ValueError(f"Collection '{name}' does not exist")
        # Optionally, you could verify that the stored collection's schema is compatible with `schema`.
        return cast(MemoryDocumentCollection[TDocument], collection)

    async def delete_collection(self, name: str) -> None:
        if name in self._collections:
            del self._collections[name]
        else:
            raise ValueError(f"Collection '{name}' does not exist")
