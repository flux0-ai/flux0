from typing import Any, List, Mapping, Optional, Protocol, Sequence, Tuple, Type, cast

import jsonpatch

from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.common import convert_patch, validate_is_total
from flux0_nanodb.projection import Projection, apply_projection
from flux0_nanodb.query import QueryFilter, matches_query
from flux0_nanodb.types import (
    DeleteResult,
    DocumentID,
    InsertOneResult,
    JSONPatchOperation,
    SortingOrder,
    TDocument,
    UpdateOneResult,
)


class Comparable(Protocol):
    def __lt__(self, other: Any) -> bool: ...


class MemoryDocumentCollection(DocumentCollection[TDocument]):
    def __init__(self, name: str, schema: Type[TDocument]) -> None:
        self._name = name
        self._schema = schema
        self._documents: list[TDocument] = []

    async def find(
        self,
        filters: Optional[QueryFilter] = None,
        projection: Optional[Mapping[str, Projection]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[Sequence[Tuple[str, SortingOrder]]] = None,
    ) -> Sequence[TDocument]:
        docs: Sequence[TDocument] = []
        # Apply filters
        if filters is None:
            docs = self._documents
        else:
            docs = [doc for doc in self._documents if matches_query(filters, doc)]

        # Sorting step: if sort is provided, sort docs on the specified fields.
        if sort is not None:
            # Process sort keys in reverse order (stable sort ensures correct overall order)
            for field, order in reversed(sort):
                docs.sort(
                    key=lambda doc: cast(Comparable, doc.get(field, None)),
                    reverse=(order == SortingOrder.DESC),
                )

        # Apply projection if given
        if projection:
            docs = [cast(TDocument, apply_projection(doc, projection)) for doc in docs]

        # Validate and apply offset
        if offset is not None:
            if offset < 0:
                raise ValueError("Offset must be non-negative")
            docs = docs[offset:]

        # Validate and apply limit
        if limit is not None:
            if limit < 0:
                raise ValueError("Limit must be non-negative")
            docs = docs[:limit]

        return docs

    async def insert_one(self, document: TDocument) -> InsertOneResult:
        self._documents.append(document)
        validate_is_total(document, self._schema)
        inserted_id: Optional[DocumentID] = document.get("id")  # type: ignore
        if inserted_id is None:
            raise ValueError("Document is missing an 'id' field")
        return InsertOneResult(acknowledged=True, inserted_id=inserted_id)

    async def update_one(
        self, filters: QueryFilter, patch: List[JSONPatchOperation], upsert: bool = False
    ) -> UpdateOneResult:
        standard_patch = convert_patch(patch)
        # Look for an existing document matching the filters.
        for i, doc in enumerate(self._documents):
            if matches_query(filters, doc):
                try:
                    updated_doc = jsonpatch.apply_patch(doc, standard_patch, in_place=False)
                except jsonpatch.JsonPatchException as e:
                    raise ValueError("Invalid JSON patch") from e
                # validate_is_total(updated_doc, self._schema)
                self._documents[i] = cast(TDocument, updated_doc)
                return UpdateOneResult(
                    acknowledged=True, matched_count=1, modified_count=1, upserted_id=None
                )
        # No matching document found.
        if upsert:
            try:
                new_doc = jsonpatch.apply_patch({}, standard_patch, in_place=False)
            except jsonpatch.JsonPatchException as e:
                raise ValueError("Invalid JSON patch for upsert") from e
            if "id" not in new_doc:
                raise ValueError("Upserted document is missing an 'id' field")
            validate_is_total(new_doc, self._schema)
            self._documents.append(cast(TDocument, new_doc))
            return UpdateOneResult(
                acknowledged=True, matched_count=0, modified_count=0, upserted_id=new_doc["id"]
            )
        return UpdateOneResult(
            acknowledged=True, matched_count=0, modified_count=0, upserted_id=None
        )

    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        for i, doc in enumerate(self._documents):
            if matches_query(filters, doc):
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
