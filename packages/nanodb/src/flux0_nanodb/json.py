import datetime
import json
from pathlib import Path
from typing import Any, List, Mapping, Optional, Protocol, Sequence, Tuple, Type, cast

import jsonpatch
from flux0_core.async_utils import RWLock

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


# Custom JSON encoder for non-serializable objects
def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime.datetime):
        return {"__type__": "datetime", "value": obj.isoformat()}
    if isinstance(obj, datetime.date):
        return {"__type__": "date", "value": obj.isoformat()}
    # Add more custom conversions as needed
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# Custom JSON decoder for objects
def _json_object_hook(obj: Any) -> Any:
    if "__type__" in obj:
        if obj["__type__"] == "datetime":
            return datetime.datetime.fromisoformat(obj["value"])
        if obj["__type__"] == "date":
            return datetime.date.fromisoformat(obj["value"])
    return obj


class JsonDocumentCollection(DocumentCollection[TDocument]):
    def __init__(self, name: str, schema: Type[TDocument], data_dir: Path) -> None:
        self._name = name
        self._schema = schema
        self._data_dir = data_dir
        self._file_path = data_dir / f"{name}.json"
        # Thread safety: Each collection has its own lock
        self._lock = RWLock()

        # Ensure the data directory exists
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the file if it doesn't exist
        if not self._file_path.exists():
            self._save_documents([])

    def _load_documents(self) -> List[TDocument]:
        """Load documents from the JSON file."""
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f, object_hook=_json_object_hook)
                return cast(List[TDocument], data)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_documents(self, documents: List[TDocument]) -> None:
        """Save documents to the JSON file."""
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False, default=_json_default)

    async def find(
        self,
        filters: Optional[QueryFilter] = None,
        projection: Optional[Mapping[str, Projection]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[Sequence[Tuple[str, SortingOrder]]] = None,
    ) -> Sequence[TDocument]:
        async with self._lock.reader_lock:
            documents = self._load_documents()
            docs: Sequence[TDocument] = []

            # Apply filters
            if filters is None:
                docs = documents
            else:
                docs = [doc for doc in documents if matches_query(filters, doc)]

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
        validate_is_total(document, self._schema)
        inserted_id: Optional[DocumentID] = document.get("id")  # type: ignore
        if inserted_id is None:
            raise ValueError("Document is missing an 'id' field")

        async with self._lock.writer_lock:
            documents = self._load_documents()
            documents.append(document)
            self._save_documents(documents)

        return InsertOneResult(acknowledged=True, inserted_id=inserted_id)

    async def update_one(
        self, filters: QueryFilter, patch: List[JSONPatchOperation], upsert: bool = False
    ) -> UpdateOneResult:
        standard_patch = convert_patch(patch)

        async with self._lock.writer_lock:
            documents = self._load_documents()

            # Look for an existing document matching the filters.
            for i, doc in enumerate(documents):
                if matches_query(filters, doc):
                    try:
                        updated_doc = jsonpatch.apply_patch(doc, standard_patch, in_place=False)
                    except jsonpatch.JsonPatchException as e:
                        raise ValueError("Invalid JSON patch") from e
                    # validate_is_total(updated_doc, self._schema)
                    documents[i] = cast(TDocument, updated_doc)
                    self._save_documents(documents)
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
                documents.append(cast(TDocument, new_doc))
                self._save_documents(documents)
                return UpdateOneResult(
                    acknowledged=True, matched_count=0, modified_count=0, upserted_id=new_doc["id"]
                )

            return UpdateOneResult(
                acknowledged=True, matched_count=0, modified_count=0, upserted_id=None
            )

    async def delete_one(self, filters: QueryFilter) -> DeleteResult[TDocument]:
        async with self._lock.writer_lock:
            documents = self._load_documents()

            for i, doc in enumerate(documents):
                if matches_query(filters, doc):
                    removed = documents.pop(i)
                    self._save_documents(documents)
                    return DeleteResult(
                        acknowledged=True, deleted_count=1, deleted_document=removed
                    )

            return DeleteResult(acknowledged=True, deleted_count=0, deleted_document=None)


class JsonDocumentDatabase(DocumentDatabase):
    def __init__(self, data_dir: str = "./data") -> None:
        """
        Initialize the JSON document database.

        Args:
            data_dir: Directory where JSON files will be stored. Defaults to "./data"
        """
        self._data_dir = Path(data_dir)
        self._collections: dict[str, JsonDocumentCollection[Any]] = {}
        # Thread safety: Database-level lock for collection management
        self._db_lock = RWLock()

        # Ensure the data directory exists
        self._data_dir.mkdir(parents=True, exist_ok=True)

    async def create_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        async with self._db_lock.writer_lock:
            if name in self._collections:
                raise ValueError(f"Collection '{name}' already exists")

            collection: JsonDocumentCollection[TDocument] = JsonDocumentCollection(
                name, schema, self._data_dir
            )
            self._collections[name] = collection
            return collection

    async def get_collection(
        self, name: str, schema: Type[TDocument]
    ) -> DocumentCollection[TDocument]:
        async with self._db_lock.reader_lock:
            # Check if collection is already loaded in memory
            if name in self._collections:
                return cast(JsonDocumentCollection[TDocument], self._collections[name])

            # Check if the JSON file exists
            file_path = self._data_dir / f"{name}.json"
            if not file_path.exists():
                raise ValueError(f"Collection '{name}' does not exist")

        # Load the collection (outside the lock to avoid holding it during I/O)
        async with self._db_lock.writer_lock:
            # Double-check in case another thread loaded it while we were waiting
            if name in self._collections:
                return cast(JsonDocumentCollection[TDocument], self._collections[name])

            collection: JsonDocumentCollection[TDocument] = JsonDocumentCollection(
                name, schema, self._data_dir
            )
            self._collections[name] = collection
            return collection

    async def delete_collection(self, name: str) -> None:
        async with self._db_lock.writer_lock:
            file_path = self._data_dir / f"{name}.json"

            # Remove from memory cache
            if name in self._collections:
                del self._collections[name]

            # Remove the file if it exists
            if file_path.exists():
                file_path.unlink()
            else:
                raise ValueError(f"Collection '{name}' does not exist")
