from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Tuple, Type, cast

import jsonpatch

if TYPE_CHECKING:
    from pymongo import AsyncMongoClient
    from pymongo.asynchronous.collection import AsyncCollection as Collection
    from pymongo.errors import DuplicateKeyError

from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.projection import Projection, apply_projection
from flux0_nanodb.query import And, Comparison, Or, QueryFilter
from flux0_nanodb.types import (
    DeleteResult,
    DocumentID,
    DocumentVersion,
    InsertOneResult,
    JSONPatchOperation,
    SortingOrder,
    TDocument,
    UpdateOneResult,
)


def _import_mongodb_dependencies() -> Tuple[
    Any, Any, Type[AsyncMongoClient[Any]], Type[DuplicateKeyError]
]:
    """Import MongoDB dependencies with proper error handling."""
    try:
        from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
        from pymongo.errors import DuplicateKeyError

        return ASCENDING, DESCENDING, AsyncMongoClient, DuplicateKeyError
    except ImportError as e:
        raise ImportError(
            "MongoDB dependencies are not installed. Install them with: pip install pymongo"
        ) from e


class MongoDocumentDatabase(DocumentDatabase):
    """MongoDB implementation of DocumentDatabase using PyMongo async API."""

    def __init__(self, client: AsyncMongoClient[Any], database_name: str):
        # Import dependencies when the class is actually used
        self._ASCENDING, self._DESCENDING, _, self._DuplicateKeyError = (
            _import_mongodb_dependencies()
        )

        self.client = client
        self.database = client[database_name]

    async def create_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        """Create a new collection with the given name and document schema."""
        # MongoDB creates collections automatically on first write
        # We'll just return a collection instance
        collection = self.database[name]
        return MongoDocumentCollection(
            collection, schema, self._ASCENDING, self._DESCENDING, self._DuplicateKeyError
        )

    async def get_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        """Retrieve an existing collection by its name and document schema."""
        # Check if collection exists
        collection_names = await self.database.list_collection_names()
        if name not in collection_names:
            raise ValueError(f"Collection '{name}' does not exist")

        collection = self.database[name]
        return MongoDocumentCollection(
            collection, schema, self._ASCENDING, self._DESCENDING, self._DuplicateKeyError
        )

    async def delete_collection(self, name: str) -> None:
        """Delete a collection by its name."""
        await self.database.drop_collection(name)


class MongoDocumentCollection(DocumentCollection[TDocument]):
    """MongoDB implementation of DocumentCollection using PyMongo async API."""

    def __init__(
        self,
        collection: Collection[Any],
        schema: Type[TDocument],
        ascending_const: Any,
        descending_const: Any,
        duplicate_key_error: Any,
    ):
        self.collection = collection
        self.schema = schema
        self._ASCENDING = ascending_const
        self._DESCENDING = descending_const
        self._DuplicateKeyError = duplicate_key_error

    def _convert_query_filter_to_mongo(self, query_filter: QueryFilter) -> Dict[str, Any]:
        """Convert our QueryFilter to MongoDB query format."""
        if isinstance(query_filter, Comparison):
            field = query_filter.path
            # Handle MongoDB's _id field mapping
            if field == "id":
                field = "_id"

            if query_filter.op == "$eq":
                return {field: query_filter.value}
            elif query_filter.op == "$ne":
                return {field: {"$ne": query_filter.value}}
            elif query_filter.op == "$gt":
                return {field: {"$gt": query_filter.value}}
            elif query_filter.op == "$gte":
                return {field: {"$gte": query_filter.value}}
            elif query_filter.op == "$lt":
                return {field: {"$lt": query_filter.value}}
            elif query_filter.op == "$lte":
                return {field: {"$lte": query_filter.value}}
            elif query_filter.op == "$in":
                return {field: {"$in": query_filter.value}}
            else:
                raise ValueError(f"Unsupported operator: {query_filter.op}")

        elif isinstance(query_filter, And):
            return {
                "$and": [
                    self._convert_query_filter_to_mongo(expr) for expr in query_filter.expressions
                ]
            }

        elif isinstance(query_filter, Or):
            return {
                "$or": [
                    self._convert_query_filter_to_mongo(expr) for expr in query_filter.expressions
                ]
            }

        else:
            raise ValueError(f"Unsupported query filter type: {type(query_filter)}")

    def _convert_projection_to_mongo(self, projection: Mapping[str, Projection]) -> Dict[str, int]:
        """Convert our Projection to MongoDB projection format."""
        mongo_projection = {}
        for field, proj_type in projection.items():
            # Handle MongoDB's _id field mapping
            mongo_field = "_id" if field == "id" else field
            mongo_projection[mongo_field] = 1 if proj_type == Projection.INCLUDE else 0
        return mongo_projection

    def _convert_sort_to_mongo(
        self, sort: Sequence[Tuple[str, SortingOrder]]
    ) -> List[Tuple[str, int]]:
        """Convert our sort specification to MongoDB sort format."""
        mongo_sort = []
        for field, order in sort:
            # Handle MongoDB's _id field mapping
            mongo_field = "_id" if field == "id" else field
            mongo_order = self._ASCENDING if order == SortingOrder.ASC else self._DESCENDING
            mongo_sort.append((mongo_field, mongo_order))
        return mongo_sort

    def _convert_from_mongo_doc(self, mongo_doc: Dict[str, Any]) -> TDocument:
        """Convert MongoDB document to our document format."""
        if mongo_doc is None:
            return None

        # Convert MongoDB's _id to our id field
        if "_id" in mongo_doc:
            mongo_doc["id"] = DocumentID(str(mongo_doc["_id"]))
            del mongo_doc["_id"]

        return cast(TDocument, mongo_doc)

    def _convert_to_mongo_doc(self, document: TDocument) -> Dict[str, Any]:
        """Convert our document format to MongoDB document."""
        mongo_doc = dict(document)

        # Convert our id field to MongoDB's _id
        if "id" in mongo_doc:
            mongo_doc["_id"] = mongo_doc["id"]
            del mongo_doc["id"]

        return mongo_doc

    async def find(
        self,
        filters: Optional[QueryFilter],
        projection: Optional[Mapping[str, Projection]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[Sequence[Tuple[str, SortingOrder]]] = None,
    ) -> Sequence[TDocument]:
        """Find all documents that match the optional filters."""
        # Build MongoDB query
        mongo_query = {}
        if filters:
            mongo_query = self._convert_query_filter_to_mongo(filters)

        # Build MongoDB projection
        mongo_projection = None
        if projection:
            mongo_projection = self._convert_projection_to_mongo(projection)

        # Start with the base query
        cursor = self.collection.find(mongo_query, mongo_projection)

        # Apply sorting
        if sort:
            mongo_sort = self._convert_sort_to_mongo(sort)
            cursor = cursor.sort(mongo_sort)

        # Apply pagination
        if offset:
            cursor = cursor.skip(offset)
        if limit:
            cursor = cursor.limit(limit)

        # Execute query and convert results
        results = await cursor.to_list(length=None)
        documents = [self._convert_from_mongo_doc(doc) for doc in results]

        # Apply projection if it was specified (MongoDB projection might not handle deep paths)
        if projection:
            projected_docs = []
            for doc in documents:
                projected_doc = apply_projection(doc, projection)
                projected_docs.append(cast(TDocument, projected_doc))
            return projected_docs

        return documents

    async def insert_one(self, document: TDocument) -> InsertOneResult:
        """Insert a single document into the collection."""
        mongo_doc = self._convert_to_mongo_doc(document)

        # Generate ID and version if not present
        if "_id" not in mongo_doc:
            mongo_doc["_id"] = str(uuid.uuid4())
        if "version" not in mongo_doc:
            mongo_doc["version"] = DocumentVersion(str(uuid.uuid4()))

        try:
            result = await self.collection.insert_one(mongo_doc)
            return InsertOneResult(
                acknowledged=result.acknowledged, inserted_id=DocumentID(str(result.inserted_id))
            )
        except self._DuplicateKeyError:
            # Handle duplicate key error
            return InsertOneResult(
                acknowledged=False, inserted_id=DocumentID(str(mongo_doc["_id"]))
            )

    async def update_one(
        self, filters: QueryFilter, patch: List[JSONPatchOperation], upsert: bool = False
    ) -> UpdateOneResult:
        """Apply a JSON Patch to a single document that matches the provided filters."""
        mongo_query = self._convert_query_filter_to_mongo(filters)

        # Find the document to patch
        existing_doc = await self.collection.find_one(mongo_query)
        if existing_doc is None and not upsert:
            return UpdateOneResult(
                acknowledged=True, matched_count=0, modified_count=0, upserted_id=None
            )

        if existing_doc is None and upsert:
            # Create a new document for upsert
            new_doc: Dict[str, Any] = {}
            # Generate ID and version
            new_doc["_id"] = str(uuid.uuid4())
            new_doc["version"] = DocumentVersion(str(uuid.uuid4()))
        else:
            # Convert from MongoDB format for patching
            # At this point, existing_doc cannot be None, so we add an assertion for the type checker
            assert existing_doc is not None
            new_doc = dict(existing_doc)
            if "_id" in new_doc:
                new_doc["id"] = str(new_doc["_id"])
                del new_doc["_id"]

        # Apply JSON patch
        patch_obj = jsonpatch.JsonPatch([dict(op) for op in patch])
        try:
            patched_doc = patch_obj.apply(new_doc)
        except jsonpatch.JsonPatchException as e:
            raise ValueError(f"Invalid JSON patch: {e}")

        # Convert back to MongoDB format
        mongo_doc = dict(patched_doc)
        if "id" in mongo_doc:
            mongo_doc["_id"] = mongo_doc["id"]
            del mongo_doc["id"]

        # Update version
        mongo_doc["version"] = DocumentVersion(str(uuid.uuid4()))

        if existing_doc is None:
            # Insert new document (upsert)
            iresult = await self.collection.insert_one(mongo_doc)
            return UpdateOneResult(
                acknowledged=iresult.acknowledged,
                matched_count=0,
                modified_count=0,
                upserted_id=DocumentID(str(iresult.inserted_id)),
            )
        else:
            # Update existing document
            uresult = await self.collection.replace_one(mongo_query, mongo_doc)
            return UpdateOneResult(
                acknowledged=uresult.acknowledged,
                matched_count=uresult.matched_count,
                modified_count=uresult.modified_count,
                upserted_id=None,
            )

    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        """Delete the first document that matches the provided filters."""
        mongo_query = self._convert_query_filter_to_mongo(filters)

        # Find the document before deleting it
        existing_doc = await self.collection.find_one(mongo_query)
        deleted_document = None
        if existing_doc:
            deleted_document = self._convert_from_mongo_doc(existing_doc)

        # Delete the document
        result = await self.collection.delete_one(mongo_query)

        return DeleteResult(
            acknowledged=result.acknowledged,
            deleted_count=result.deleted_count,
            deleted_document=deleted_document,
        )


def create_client(uri: str) -> AsyncMongoClient[Any]:
    """Create a MongoDB client."""
    _, _, AsyncMongoClient, _ = _import_mongodb_dependencies()
    return AsyncMongoClient(uri)
