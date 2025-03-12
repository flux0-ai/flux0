from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Mapping, Optional, Sequence, Type

from flux0_nanodb.projection import Projection
from flux0_nanodb.query import QueryFilter
from flux0_nanodb.types import DeleteResult, InsertOneResult, TDocument


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
    ) -> Sequence[TDocument]:
        """
        Find all documents that match the optional filters.
        Optionally apply a projection to return only specified fields.
        Supports pagination via limit and offset.
        """
        pass

    @abstractmethod
    async def insert_one(self, document: TDocument) -> InsertOneResult:
        """
        Insert a single document into the collection.
        """
        pass

    @abstractmethod
    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        """
        Delete the first document that matches the provided filters.
        """
        pass
