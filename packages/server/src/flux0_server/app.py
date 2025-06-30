import asyncio
import os
import sysconfig
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from flux0_api.agents import (
    mount_create_agent_route,
    mount_list_agents_route,
    mount_retrieve_agent_route,
)
from flux0_api.sessions import (
    mount_create_event_and_stream_route,
    mount_create_session_route,
    mount_list_session_events_route,
    mount_list_sessions_route,
    mount_retrieve_session_route,
)
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id
from flux0_core.logging import Logger
from lagom import Container
from starlette.types import ASGIApp


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Any) -> Response:
        assert isinstance(self.directory, str), "Static directory must be a string"

        full_path = os.path.join(self.directory, path)

        # If the file exists, serve it
        if os.path.isfile(full_path):
            return await super().get_response(path, scope)

        # If the file does NOT exist, serve `index.html`
        return await super().get_response("index.html", scope)


def static_path() -> str:
    if os.environ.get("FLUX0_STATIC_DIR"):
        return os.environ["FLUX0_STATIC_DIR"]

    shared_data_dir = sysconfig.get_path("data")
    static_dir = os.path.join(shared_data_dir, "flux0-chat", "static")
    return static_dir


async def create_api_app(c: Container) -> ASGIApp:
    logger = c[Logger]
    correlator = c[ContextualCorrelator]

    api_app = FastAPI(
        title="Flux0 AI Agent API",
        summary="A flexible API for managing AI-driven agents, sessions, and event streaming in real time.",
        description=(
            "The Flux0 API enables developers to create and manage AI agents, interact with them via sessions, "
            "and handle event streaming using JSONPatch (RFC 6902). It is designed to support multi-agent workflows, "
            "facilitate LLM-agnostic integrations, and provide structured interactions with AI-powered assistants. "
            "The API is ideal for orchestrating intelligent assistants, tracking interactions, and ensuring dynamic "
            "and responsive AI applications."
        ),
        servers=[
            {"url": "http://localhost:8080", "description": "Local server"},
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

    static_dir = static_path()
    if os.path.isdir(static_dir):
        api_app.mount("/chat", SPAStaticFiles(directory=static_dir), name="static")

    @api_app.get("/", include_in_schema=False)
    async def root() -> Response:
        return RedirectResponse("/chat")

    api_router = APIRouter(prefix="/api")

    api_agents_router = APIRouter(prefix="/agents")
    mount_create_agent_route(api_agents_router)
    mount_retrieve_agent_route(api_agents_router)
    mount_list_agents_route(api_agents_router)
    api_router.include_router(api_agents_router)

    api_sessions_router = APIRouter(prefix="/sessions")
    mount_create_session_route(api_sessions_router)
    mount_retrieve_session_route(api_sessions_router)
    mount_list_sessions_route(api_sessions_router)
    mount_create_event_and_stream_route(api_sessions_router)
    mount_list_session_events_route(api_sessions_router)
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
