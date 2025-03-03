from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from flux0_api.auth import AuthHandler, NoopAuthHandler
from flux0_core.storage.nanodb_memory import UserDocumentStore
from flux0_core.users import User, UserId, UserStore
from flux0_nanodb.api import DocumentDatabase
from flux0_nanodb.memory import MemoryDocumentDatabase
from lagom import Container


@pytest.fixture
def user() -> User:
    return User(
        id=UserId("v9pg5Zv3h4"),
        sub="john.doe",
        name="John Doe",
        email="john.doe@acme.io",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def document_db() -> AsyncGenerator[DocumentDatabase, None]:
    db = MemoryDocumentDatabase()
    yield db


@pytest.fixture
async def user_store(
    document_db: DocumentDatabase,
) -> AsyncGenerator[UserStore, None]:
    async with UserDocumentStore(db=document_db) as store:
        yield store


@pytest.fixture
def container(user_store: UserStore) -> Container:
    c = Container()
    c[UserStore] = user_store
    c[AuthHandler] = NoopAuthHandler
    return c


@pytest.fixture
def fastapi(container: Container) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.container = container
        yield

    app = FastAPI(lifespan=lifespan)

    return app
