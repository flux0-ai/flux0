from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Annotated, Any, NewType

import jwt
import requests
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from flux0_core.users import User, UserStore
from flux0_server.settings import AuthType, settings
from pydantic import BaseModel

from flux0_api.dependency_injection import resolve_dependency


class AuthHandler(ABC):
    @abstractmethod
    async def __call__(self, request: Request) -> User:
        """Auth handler that returns a user object or raises an HTTPException."""


AuthHandlers = NewType("AuthHandlers", AuthHandler)


NOOP_AUTH_HANDLER_DEFAULT_SUB = "anonymous"
NOOP_AUTH_HANDLER_DEFAULT_NAME = NOOP_AUTH_HANDLER_DEFAULT_SUB.capitalize()


class NoopAuthSettings(BaseModel):
    auth_type: AuthType = AuthType.NOOP


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


class JWTAuthBase(AuthHandler):
    user_store: UserStore

    def __init__(self, user_store: UserStore):
        self.user_store = user_store

    async def __call__(self, request: Request) -> User:
        http_bearer = await HTTPBearer()(request)
        if not http_bearer:
            raise HTTPException(status_code=401, detail="Invalid token")
        token = http_bearer.credentials

        try:
            payload = self.decode_token(token, self.get_decode_key(token))
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail=str(e))

        sub = payload["sub"]
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await self.user_store.read_user_by_sub(sub)
        if not user:
            name = payload.get("name", NOOP_AUTH_HANDLER_DEFAULT_NAME)
            user = await self.user_store.create_user(sub=sub, name=name)

        return user

    @abstractmethod
    def decode_token(self, token: str, decode_key: str) -> dict[str, str]: ...

    @abstractmethod
    def get_decode_key(self, token: str) -> str: ...


class JWTAuthOIDC(JWTAuthBase):
    """Auth handler that uses OIDC discovery to get the decode key."""

    def decode_token(self, token: str, decode_key: str) -> dict[str, str]:
        alg = self._decode_complete_unverified(token)["header"]["alg"]
        decoded = jwt.decode(
            token,
            decode_key,
            issuer=settings.jwt_oidc_issuer,
            audience=settings.jwt_oidc_audience,
            algorithms=[alg.upper()],
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        return dict(decoded)

    def get_decode_key(self, token: str) -> str:
        unverified = self._decode_complete_unverified(token)
        issuer = unverified["payload"].get("iss")
        kid = unverified["header"].get("kid")
        signing_key = self._get_jwk_client(issuer).get_signing_key(kid)
        return str(signing_key.key)

    @lru_cache
    def _decode_complete_unverified(self, token: str) -> dict[str, Any]:
        return jwt.api_jwt.decode_complete(token, options={"verify_signature": False})

    @lru_cache
    def _get_jwk_client(self, issuer: str) -> jwt.PyJWKClient:
        """
        lru_cache ensures a single instance of PyJWKClient per issuer. This is
        so that we can take advantage of jwks caching (and invalidation) handled
        by PyJWKClient.
        """
        url = issuer.rstrip("/") + "/.well-known/openid-configuration"
        config = requests.get(url).json()
        return jwt.PyJWKClient(config["jwks_uri"], cache_jwk_set=True)


async def auth_user(request: Request) -> User:
    """FastAPI dependency that returns an authenticated user object."""
    auth_handler = resolve_dependency(request, AuthHandler)
    return await auth_handler(request)


AuthedUser = Annotated[User, Depends(auth_user)]
