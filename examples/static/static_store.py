from datetime import datetime, timezone
from typing import TypedDict

from flux0_core.ids import gen_id
from flux0_nanodb.api import DocumentCollection, DocumentDatabase
from flux0_nanodb.types import DocumentID, DocumentVersion


class _StaticDocumentExample(TypedDict, total=False):
    id: DocumentID
    version: DocumentVersion
    created_at: datetime


class ExampleStaticDocumentStore:
    VERSION = DocumentVersion("0.0.0")

    def __init__(self, db: DocumentDatabase):
        self.db = db
        self._col: DocumentCollection[_StaticDocumentExample]

    async def setup(self):
        self._col = await self.db.create_collection("example_static", _StaticDocumentExample)

    async def create(self) -> _StaticDocumentExample:
        created_at = datetime.now(timezone.utc)
        doc = _StaticDocumentExample(
            id=DocumentID(gen_id()),
            version=self.VERSION,
            created_at=created_at,
        )
        await self._col.insert_one(document=doc)
        return doc
