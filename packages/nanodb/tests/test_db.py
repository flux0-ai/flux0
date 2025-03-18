import uuid
from typing import Any, List, NotRequired, TypedDict

import pytest

# Imports from our implementation and query language.
from flux0_nanodb.api import (
    DocumentCollection,
    DocumentDatabase,
)
from flux0_nanodb.memory import MemoryDocumentDatabase
from flux0_nanodb.projection import Projection
from flux0_nanodb.query import Comparison, QueryFilter
from flux0_nanodb.types import (
    DeleteResult,
    DocumentID,
    DocumentVersion,
    InsertOneResult,
    JSONPatchOperation,
    SortingOrder,
)


# A test document that extends our base Document.
class SimpleDocument(TypedDict, total=False):
    name: str
    value: int
    profile: NotRequired[dict[str, Any]]
    settings: NotRequired[dict[str, Any]]
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
    doc = SimpleDocument(id=doc_id, version=version, name="Bob", value=100, profile={}, settings={})
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
    doc = SimpleDocument(
        id=doc_id, version=version, name="Carol", value=10, profile={}, settings={}
    )
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


@pytest.mark.asyncio
async def test_find_with_pagination(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert multiple documents with predictable values
    docs = []
    for i in range(5):
        doc_id = DocumentID(str(uuid.uuid4()))
        version = DocumentVersion("1.0")
        doc = SimpleDocument(
            id=doc_id, version=version, name=f"User{i}", value=i, profile={}, settings={}
        )
        docs.append(doc)
        await collection.insert_one(doc)

    # Verify full retrieval (sanity check)
    found_all = await collection.find(filters=None)
    assert len(found_all) == 5  # Ensure all documents are present
    assert found_all == docs  # Ensure the documents are in the correct order

    # Test with offset = 1, limit = 3
    found = await collection.find(filters=None, limit=3, offset=1)
    assert len(found) == 3  # Should return 3 documents
    assert found == docs[1:4]  # Expecting docs[1], docs[2], docs[3]

    # Test with offset = 4, limit = 10 (limit greater than remaining docs)
    found = await collection.find(filters=None, limit=10, offset=4)
    assert len(found) == 1  # Only one document remains
    assert found == [docs[4]]  # Expecting the last document only

    # Test with offset = 5 (beyond range)
    found = await collection.find(filters=None, limit=3, offset=5)
    assert len(found) == 0  # Should return no documents


@pytest.mark.asyncio
async def test_find_with_sorting(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert documents in an unsorted order.
    docs = []
    # Document 1: value=30, name="Bob"
    doc1 = SimpleDocument(
        id=DocumentID(str(uuid.uuid4())),
        version=DocumentVersion("1.0"),
        name="Bob",
        value=30,
        profile={},
        settings={},
    )
    docs.append(doc1)
    # Document 2: value=20, name="Alice"
    doc2 = SimpleDocument(
        id=DocumentID(str(uuid.uuid4())),
        version=DocumentVersion("1.0"),
        name="Alice",
        value=20,
        profile={},
        settings={},
    )
    docs.append(doc2)
    # Document 3: value=40, name="Carol"
    doc3 = SimpleDocument(
        id=DocumentID(str(uuid.uuid4())),
        version=DocumentVersion("1.0"),
        name="Carol",
        value=40,
        profile={},
        settings={},
    )
    docs.append(doc3)

    for doc in docs:
        await collection.insert_one(doc)

    # Sort by "value" in ascending order.
    sorted_by_value = await collection.find(filters=None, sort=[("value", SortingOrder.ASC)])
    assert sorted_by_value == [doc2, doc1, doc3]

    # Sort by "name" in descending order.
    sorted_by_name = await collection.find(filters=None, sort=[("name", SortingOrder.DESC)])
    # Expected order: "Carol" > "Bob" > "Alice"
    assert sorted_by_name == [doc3, doc1, doc2]

    # Sort by "value" ascending then by "name" descending (if needed for tie-breakers)
    # For demonstration, create two documents with the same value.
    doc4 = SimpleDocument(
        id=DocumentID(str(uuid.uuid4())),
        version=DocumentVersion("1.0"),
        name="Zoe",
        value=25,
        profile={},
        settings={},
    )
    doc5 = SimpleDocument(
        id=DocumentID(str(uuid.uuid4())),
        version=DocumentVersion("1.0"),
        name="Anna",
        value=25,
        profile={},
        settings={},
    )
    await collection.insert_one(doc4)
    await collection.insert_one(doc5)

    # Now sort by "value" ascending then by "name" descending.
    sorted_multi = await collection.find(
        filters=None, sort=[("value", SortingOrder.ASC), ("name", SortingOrder.DESC)]
    )
    # Expected order:
    # - First: document with value=20 (doc2),
    # - Then the two with value=25 sorted by name descending: "Zoe" (doc4) comes before "Anna" (doc5),
    # - Followed by: document with value=30 (doc1),
    # - And lastly: document with value=40 (doc3).
    expected = [doc2, doc4, doc5, doc1, doc3]
    assert sorted_multi == expected


@pytest.mark.asyncio
async def test_update_replace_field(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(
        id=doc_id, version=version, name="Alice", value=10, profile={}, settings={}
    )
    await collection.insert_one(doc)

    # Use update_one to replace the "value" field.
    patch: List[JSONPatchOperation] = [{"op": "replace", "path": "/value", "value": 20}]
    result = await collection.update_one(
        filters=Comparison(path="id", op="$eq", value=doc_id), patch=patch
    )
    assert result.matched_count == 1
    found = await collection.find(Comparison(path="id", op="$eq", value=doc_id))
    assert found[0].get("value") == 20


@pytest.mark.asyncio
async def test_update_add_nested_field(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document with no settings.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(id=doc_id, version=version, name="Bob", value=50, profile={}, settings={})
    await collection.insert_one(doc)

    # Use update_one to add a nested field in settings.
    patch: List[JSONPatchOperation] = [{"op": "add", "path": "/settings/theme", "value": "dark"}]
    result = await collection.update_one(
        filters=Comparison(path="id", op="$eq", value=doc_id), patch=patch
    )
    assert result.matched_count == 1
    found = await collection.find(Comparison(path="id", op="$eq", value=doc_id))
    assert "settings" in found[0] and found[0]["settings"].get("theme") == "dark"


@pytest.mark.asyncio
async def test_update_remove_field(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document with a 'name' field.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(
        id=doc_id, version=version, name="Carol", value=75, profile={}, settings={}
    )
    await collection.insert_one(doc)

    # Use update_one to remove the 'name' field.
    patch: List[JSONPatchOperation] = [{"op": "remove", "path": "/name"}]
    result = await collection.update_one(
        filters=Comparison(path="id", op="$eq", value=doc_id), patch=patch
    )
    assert result.matched_count == 1
    found = await collection.find(Comparison(path="id", op="$eq", value=doc_id))
    assert "name" not in found[0]


@pytest.mark.asyncio
async def test_update_replace_nested_value(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document with nested profile information.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(
        id=doc_id,
        version=version,
        name="Dave",
        value=100,
        profile={"address": {"city": "Old Town"}},
    )
    await collection.insert_one(doc)

    # Use update_one to replace the nested city value.
    patch: List[JSONPatchOperation] = [
        {"op": "replace", "path": "/profile/address/city", "value": "New York"}
    ]
    result = await collection.update_one(
        filters=Comparison(path="id", op="$eq", value=doc_id), patch=patch
    )
    assert result.matched_count == 1
    found = await collection.find(Comparison(path="id", op="$eq", value=doc_id))
    assert (
        "profile" in found[0]
        and "address" in found[0]["profile"]
        and found[0]["profile"]["address"]["city"] == "New York"
    )


@pytest.mark.asyncio
async def test_update_upsert_document(collection: DocumentCollection[SimpleDocument]) -> None:
    # Attempt to update a non-existent document; upsert should create a new one.
    new_doc_id = DocumentID(str(uuid.uuid4()))
    patch: List[JSONPatchOperation] = [
        {"op": "add", "path": "/id", "value": new_doc_id},
        {"op": "add", "path": "/name", "value": "Eve"},
        {"op": "add", "path": "/value", "value": 200},
    ]
    result = await collection.update_one(
        filters=Comparison(path="id", op="$eq", value=new_doc_id), patch=patch, upsert=True
    )
    assert result.matched_count == 0
    assert result.upserted_id == new_doc_id
    found = await collection.find(Comparison(path="id", op="$eq", value=new_doc_id))
    assert len(found) == 1
    assert found[0].get("name") == "Eve"
    assert found[0].get("value") == 200


@pytest.mark.asyncio
async def test_update_invalid_patch(collection: DocumentCollection[SimpleDocument]) -> None:
    # Insert a document.
    doc_id = DocumentID(str(uuid.uuid4()))
    version = DocumentVersion("1.0")
    doc = SimpleDocument(id=doc_id, version=version, name="Frank", value=300)
    await collection.insert_one(doc)

    # Use an invalid patch (e.g., trying to replace a non-existent path without add).
    patch: List[JSONPatchOperation] = [{"op": "replace", "path": "/nonexistent", "value": "oops"}]
    with pytest.raises(ValueError):
        await collection.update_one(
            filters=Comparison(path="id", op="$eq", value=doc_id), patch=patch
        )
    docs = await collection.find(Comparison(path="id", op="$eq", value=doc_id))
    assert doc == docs[0]
