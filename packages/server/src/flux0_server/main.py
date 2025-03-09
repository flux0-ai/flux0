import asyncio
import importlib
import os
import sys
import traceback
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Iterable

import toml
import uvicorn
from flux0_api.auth import AuthHandler, AuthType, NoopAuthHandler
from flux0_api.session_service import SessionService
from flux0_core.agents import AgentStore
from flux0_core.background_tasks_service import BackgroundTaskService
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import Logger, LogLevel, StdoutLogger
from flux0_core.sessions import SessionStore
from flux0_core.storage.nanodb_memory import (
    AgentDocumentStore,
    SessionDocumentStore,
    UserDocumentStore,
)
from flux0_core.storage.types import StorageType
from flux0_core.users import UserStore
from flux0_nanodb.memory import MemoryDocumentDatabase
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.emitter.memory import MemoryEventEmitter
from flux0_stream.store.memory import MemoryEventStore
from lagom import Container, Singleton
from starlette.types import ASGIApp

from flux0_server.app import create_api_app
from flux0_server.container_factory import ContainerAgentRunnerFactory
from flux0_server.settings import EnvType, Settings, settings
from flux0_server.version import VERSION

DEFAULT_PORT = 8080
SERVER_ADDRESS = "http://localhost"
CORRELATOR = ContextualCorrelator()
LOGGER = StdoutLogger(
    correlator=CORRELATOR, log_level=LogLevel.INFO, json=settings.env != EnvType.DEVELOPMENT
)
BACKGROUND_TASK_SERVICE: BackgroundTaskService


class StartupError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@asynccontextmanager
async def setup_container(
    settings: Settings, exit_stack: AsyncExitStack
) -> AsyncIterator[Container]:
    c = Container()

    c[ContextualCorrelator] = CORRELATOR
    c[Logger] = LOGGER
    c[Logger].set_level(settings.log_level)

    if settings.stores_type == StorageType.NANODB_MEMORY:
        db = MemoryDocumentDatabase()
        event_store = await exit_stack.enter_async_context(MemoryEventStore())
        c[EventEmitter] = Singleton(
            await exit_stack.enter_async_context(
                MemoryEventEmitter(event_store=event_store, logger=LOGGER)
            )
        )
        global BACKGROUND_TASK_SERVICE
        BACKGROUND_TASK_SERVICE = await exit_stack.enter_async_context(
            BackgroundTaskService(LOGGER)
        )
        user_store = await exit_stack.enter_async_context(UserDocumentStore(db))
        agent_store = await exit_stack.enter_async_context(AgentDocumentStore(db))
        session_store = await exit_stack.enter_async_context(SessionDocumentStore(db))
        c[SessionService] = SessionService(
            contextual_correlator=CORRELATOR,
            logger=LOGGER,
            agent_store=agent_store,
            session_store=session_store,
            background_task_service=BACKGROUND_TASK_SERVICE,
            agent_runner_factory=ContainerAgentRunnerFactory(c),
            event_emitter=c[EventEmitter],
        )
        c[UserStore] = user_store
        c[AgentStore] = agent_store
        c[SessionStore] = session_store
    else:
        raise StartupError(f"Unsupported storage type: {settings.stores_type}")

    if settings.auth_type == AuthType.NOOP:
        c[AuthHandler] = NoopAuthHandler(user_store=c[UserStore])
    else:
        raise StartupError(f"Unsupported auth type: {settings.auth_type}")

    yield c


@asynccontextmanager
async def load_modules(
    container: Container,
    modules: Iterable[str],
) -> AsyncIterator[None]:
    imported_modules = []

    for module_path in modules:
        print("Current Working Directory:", os.getcwd())
        module = importlib.import_module(module_path)
        if not hasattr(module, "init_module") or not hasattr(module, "shutdown_module"):
            raise StartupError(
                f"Module '{module.__name__}' must define init_module(container: lagom.Container) and shutdown_module()"
            )
        imported_modules.append(module)

    for m in imported_modules:
        LOGGER.info(f"Initializing module '{m.__name__}'")
        await m.init_module(container)

    try:
        yield
    finally:
        for m in reversed(imported_modules):
            LOGGER.info(f"Shutting down module '{m.__name__}'")
            await m.shutdown_module()


async def serve_app(
    app: ASGIApp,
    port: int,
) -> None:
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="critical",
        timeout_graceful_shutdown=1,
    )
    server = uvicorn.Server(config)

    try:
        LOGGER.info("Server is ready")
        await server.serve()
        await asyncio.sleep(0)  # Ensures the cancellation error can be raised
    except (KeyboardInterrupt, asyncio.CancelledError):
        await BACKGROUND_TASK_SERVICE.cancel_all(reason="Server shutting down")
    except BaseException as e:
        LOGGER.critical(traceback.format_exc())
        LOGGER.critical(e.__class__.__name__ + ": " + str(e))
        sys.exit(1)
    finally:
        LOGGER.info("Server is shutting down gracefuly")


async def get_module_list_from_config() -> list[str]:
    config_file = Path("flux0.toml")

    if config_file.exists():
        config = toml.load(config_file)
        # Expecting structure of:
        # [flux0]
        # modules = ["module_1", "module_2"]
        return list(config.get("flux0", {}).get("modules", []))

    return []


@asynccontextmanager
async def setup_app(settings: Settings) -> AsyncIterator[ASGIApp]:
    exit_stack = AsyncExitStack()

    async with (
        setup_container(settings, exit_stack) as container,
        exit_stack,
    ):
        modules = set(await get_module_list_from_config() + settings.modules)
        if modules:
            await exit_stack.enter_async_context(load_modules(container, modules))
        else:
            LOGGER.debug("No external modules defined")
        yield await create_api_app(container)


async def start_server(settings: Settings) -> None:
    LOGGER.info(f"Flux0 server version {VERSION}")
    async with setup_app(settings) as app:
        await serve_app(
            app,
            settings.port,
        )


def main() -> None:
    asyncio.run(start_server(settings))


if __name__ == "__main__":
    main()
