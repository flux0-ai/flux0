from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from flux0_api.auth import (
    NOOP_AUTH_HANDLER_DEFAULT_NAME,
    NOOP_AUTH_HANDLER_DEFAULT_SUB,
    AuthedUser,
    NoopAuthHandler,
)
from flux0_core.users import User, UserId, UserStore
from starlette.datastructures import Headers, MutableHeaders


async def test_noop_auth_handler_no_user_found(user: User) -> None:
    # Mock user store
    user_store = AsyncMock(spec=UserStore)

    # Simulate user not found in the database
    user_store.read_user_by_sub.return_value = None

    # Mock user creation response
    user_store.create_user.return_value = User(
        id=UserId("o4pg3Ki5h9"),
        sub=NOOP_AUTH_HANDLER_DEFAULT_SUB,
        name=NOOP_AUTH_HANDLER_DEFAULT_SUB.capitalize(),
        email="anonymous@acme.io",
        created_at=datetime.now(timezone.utc),
    )

    # Initialize the NoopHandler
    handler = NoopAuthHandler(user_store)

    # Mock FastAPI Request with empty cookies
    request = Request({"type": "http", "headers": Headers().raw})

    # Call the NoopHandler
    user = await handler(request)

    # Assertions
    assert user.sub == NOOP_AUTH_HANDLER_DEFAULT_SUB
    user_store.read_user_by_sub.assert_awaited_once_with(NOOP_AUTH_HANDLER_DEFAULT_SUB)
    user_store.create_user.assert_awaited_once_with(
        sub=NOOP_AUTH_HANDLER_DEFAULT_SUB, name=NOOP_AUTH_HANDLER_DEFAULT_NAME
    )


async def test_noop_handler_returns_existing_user(user: User) -> None:
    """Test NoopHandler when an existing user is found in the database."""

    # Mock user store
    user_store = AsyncMock(spec=UserStore)

    # Simulate an existing user
    user_store.read_user_by_sub.return_value = user

    # Initialize NoopHandler
    handler = NoopAuthHandler(user_store)

    # Mock FastAPI Request with a cookie
    headers = MutableHeaders()
    headers["cookie"] = f"flux0_user_sub={user.sub}"
    request = Request({"type": "http", "headers": headers.raw})

    # Call NoopHandler
    user = await handler(request)

    # Assertions
    assert user.sub == user.sub
    assert user.name == user.name
    user_store.read_user_by_sub.assert_awaited_once_with(user.sub)
    user_store.create_user.assert_not_awaited()  # No new user should be created


async def test_fastapi_authed_user_dependency(fastapi: FastAPI, user: User) -> None:
    """Test the AuthedUser dependency by mocking auth_user."""

    @fastapi.get("/me")
    async def get_current_user(authedUser: AuthedUser) -> dict[str, str]:
        """Test route that returns the authenticated user's details."""
        return {"id": user.id, "sub": user.sub, "name": user.name}

    with TestClient(fastapi) as client:
        client = TestClient(fastapi)
        # Make a request to the test route
        response = client.get("/me")
        # Validate response
        assert response.status_code == 200
        assert response.json() == {"id": user.id, "sub": user.sub, "name": user.name}
