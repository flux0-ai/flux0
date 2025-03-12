import uuid
from typing import TypedDict

import pytest

# Imports from our implementation and query language.
from flux0_nanodb.api import (
    DocumentCollection,
    DocumentDatabase,
)
from flux0_nanodb.memory import MemoryDocumentDatabase
from flux0_nanodb.projection import Projection
from flux0_nanodb.query import Comparison, QueryFilter
from flux0_nanodb.types import DeleteResult, DocumentID, DocumentVersion, InsertOneResult


# A test document that extends our base Document.
class SimpleDocument(TypedDict, total=False):
    name: str
    value: int
    id: DocumentID
    version: DocumentVersion


# Fixture to provide a DocumentDatabase instance.
@pytest.fixture
def db() -> DocumentDatabase:
    return MemoryDocumentDatabase()


# Fixture to provide a collection of TestDocument.
@pytest.fixture
async def collection(db: DocumentDatabase) -> DocumentCollection[SimpleDocument]:
    return await db.create_collection("test_collection", SimpleDocument)


@pytest.mark.asyncio
async def test_insert_and_find(collection: DocumentCollection[SimpleDocument]) -> None:
    # Create and insert a document.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(id=doc_id, version=version, name="Alice", value=42)
    result: InsertOneResult = await collection.insert_one(doc)
    assert result.acknowledged
    assert result.inserted_id == doc_id

    # Query for the document by name.
    query: QueryFilter = Comparison(path="name", op="$eq", value="Alice")
    found = await collection.find(query)
    assert len(found) == 1
    assert found[0] == doc

    # Query for the document with projection.
    found = await collection.find(query, projection={"name": Projection.INCLUDE})
    assert found[0] == SimpleDocument(name="Alice")


@pytest.mark.asyncio
async def test_delete_document(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document and then delete it.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(id=doc_id, version=version, name="Bob", value=100)
    await collection.insert_one(doc)

    query: QueryFilter = Comparison(path="name", op="$eq", value="Bob")
    delete_result: DeleteResult[SimpleDocument] = await collection.delete_one(query)
    assert delete_result.acknowledged
    assert delete_result.deleted_count == 1
    assert delete_result.deleted_document == doc

    # Verify that the document is no longer found.
    found = await collection.find(query)
    assert len(found) == 0


@pytest.mark.asyncio
async def test_find_no_results(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(id=doc_id, version=version, name="Carol", value=10)
    await collection.insert_one(doc)

    # Query with a filter that should not match.
    query: QueryFilter = Comparison(path="name", op="$eq", value="Dave")
    found = await collection.find(query)
    assert len(found) == 0


@pytest.mark.asyncio
async def test_get_nonexistent_collection(db: DocumentDatabase) -> None:
    # Attempting to retrieve a collection that doesn't exist should raise a ValueError.
    with pytest.raises(ValueError):
        await db.get_collection("nonexistent", SimpleDocument)


@pytest.mark.asyncio
async def test_delete_collection(db: DocumentDatabase) -> None:
    # Create and then delete a collection.
    _ = await db.create_collection("to_delete", SimpleDocument)
    await db.delete_collection("to_delete")
    with pytest.raises(ValueError):
        await db.get_collection("to_delete", SimpleDocument)
