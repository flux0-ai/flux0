import asyncio
from typing import Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response, status
from flux0_api.agents import (
    mount_create_agent_route,
    mount_list_agents_route,
    mount_retrieve_agent_route,
)
from flux0_api.sessions import (
    mount_create_event_and_stream_route,
    mount_create_session_route,
    mount_retrieve_session_route,
)
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id
from flux0_core.logging import Logger
from lagom import Container
from starlette.types import ASGIApp


async def create_api_app(c: Container) -> ASGIApp:
    logger = c[Logger]
    correlator = c[ContextualCorrelator]

    api_app = FastAPI(
        servers=[
            {"url": "http://127.0.0.1:8080", "description": "Local server"},
        ],
    )

    api_app.state.container = c

    @api_app.middleware("http")
    async def handle_cancellation(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except asyncio.CancelledError:
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    @api_app.middleware("http")
    async def add_correlation_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = gen_id()
        with correlator.scope(f"RID({request_id})"):
            with logger.operation(f"HTTP Request: {request.method} {request.url.path}"):
                return await call_next(request)

    api_router = APIRouter(prefix="/api")

    api_agents_router = APIRouter(prefix="/agents")
    mount_create_agent_route(api_agents_router)
    mount_retrieve_agent_route(api_agents_router)
    mount_list_agents_route(api_agents_router)
    api_router.include_router(api_agents_router)

    api_sessions_router = APIRouter(prefix="/sessions")
    mount_create_session_route(api_sessions_router)
    mount_retrieve_session_route(api_sessions_router)
    mount_create_event_and_stream_route(api_sessions_router)
    api_router.include_router(api_sessions_router)

    api_app.include_router(api_router)

    @api_app.middleware("http")
    async def handle_cancelled_error(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except asyncio.CancelledError:
            logger.warning("Request was cancelled.")
            raise
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            raise

    return api_app
