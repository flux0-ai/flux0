from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated, NewType

from fastapi import Depends, Request
from flux0_core.users import User, UserStore

from flux0_api.dependency_injection import resolve_dependency


class AuthHandler(ABC):
    @abstractmethod
    async def __call__(self, request: Request) -> User:
        """Auth handler that returns a user object or raises an HTTPException."""


AuthHandlers = NewType("AuthHandlers", AuthHandler)


class AuthType(Enum):
    NOOP = "noop"


NOOP_AUTH_HANDLER_DEFAULT_SUB = "anonymous"
NOOP_AUTH_HANDLER_DEFAULT_NAME = NOOP_AUTH_HANDLER_DEFAULT_SUB.capitalize()


class NoopAuthHandler(AuthHandler):
    _default_sub = NOOP_AUTH_HANDLER_DEFAULT_SUB
    user_store: UserStore

    def __init__(self, user_store: UserStore):
        self.user_store = user_store

    async def __call__(self, request: Request) -> User:
        """No-op auth handler that always returns an anonymous user."""
        sub = request.cookies.get("flux0_user_sub") or self._default_sub

        user = await self.user_store.read_user_by_sub(sub)
        if not user:
            user = await self.user_store.create_user(
                sub=sub, name=NOOP_AUTH_HANDLER_DEFAULT_SUB.capitalize()
            )

        return user


async def auth_user(request: Request) -> User:
    """FastAPI dependency that returns an authenticated user object."""
    auth_handler = resolve_dependency(request, AuthHandler)
    return await auth_handler(request)


AuthedUser = Annotated[User, Depends(auth_user)]
