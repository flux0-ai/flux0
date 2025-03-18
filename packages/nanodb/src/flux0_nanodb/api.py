from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Mapping, Optional, Sequence, Tuple, Type

from flux0_nanodb.projection import Projection
from flux0_nanodb.query import QueryFilter
from flux0_nanodb.types import (
    DeleteResult,
    InsertOneResult,
    JSONPatchOperation,
    SortingOrder,
    TDocument,
    UpdateOneResult,
)


class DocumentDatabase(ABC):
    @abstractmethod
    async def create_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        """
        Create a new collection with the given name and document schema.
        """
        pass

    @abstractmethod
    async def get_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        """
        Retrieve an existing collection by its name and document schema.
        """
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """
        Delete a collection by its name.
        """
        pass


class DocumentCollection(ABC, Generic[TDocument]):
    @abstractmethod
    async def find(
        self,
        filters: Optional[QueryFilter],
        projection: Optional[Mapping[str, Projection]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[Sequence[Tuple[str, SortingOrder]]] = None,
    ) -> Sequence[TDocument]:
        """
        Find all documents that match the optional filters.
        Optionally apply a projection, pagination, and sorting.

        - `sort` is a list of tuples where:
          - The first element is the field name.
          - The second element is the sorting order (`SortOrder.ASC` for ascending or `SortOrder.DESC` for descending).

        Sorting is applied after filtering but before pagination.
        """
        pass

    @abstractmethod
    async def insert_one(self, document: TDocument) -> InsertOneResult:
        """
        Insert a single document into the collection.
        """
        pass

    @abstractmethod
    async def update_one(
        self, filters: QueryFilter, patch: List[JSONPatchOperation], upsert: bool = False
    ) -> UpdateOneResult:
        """
        Apply a JSON Patch (RFC 6902) to a single document that matches the provided filters.
        If upsert is True and no document matches, insert a new document.

        Parameters:
            filters (QueryFilter): Query to match a document.
            patch (List[JSONPatchOperation]): JSON Patch operations in a type-safe structured format.
            upsert (bool): If True, insert a new document if no match is found.

        Returns:
            UpdateOneResult: Metadata about the update operation.
        """
        pass

    @abstractmethod
    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        """
        Delete the first document that matches the provided filters.
        """
        pass
