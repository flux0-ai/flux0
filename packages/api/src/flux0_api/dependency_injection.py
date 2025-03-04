from typing import Optional, Type, TypeVar, cast

import inflection
from fastapi import HTTPException, Request
from flux0_core.agents import AgentStore
from flux0_core.sessions import SessionStore
from flux0_core.users import UserStore
from flux0_stream.emitter.api import EventEmitter

from flux0_api.session_service import SessionService

# Try to import lagom
try:
    from lagom import Container

    LAGOM_AVAILABLE = True
except ImportError:
    LAGOM_AVAILABLE = False


T = TypeVar("T")  # Generic type variable for dependencies


def resolve_dependency(request: Request, dependency_type: Type[T]) -> T:
    """
    Resolves a dependency, checking first in Lagom and falling back to FastAPI app.state.

    Args:
        request (Request): The FastAPI request object.
        dependency_type (Type[T]): The type of the dependency to resolve.

    Returns:
        T: The resolved dependency instance.

    Raises:
        HTTPException: If the dependency cannot be found in either Lagom or app.state.
    """
    container: Optional[Container] = (
        getattr(request.app.state, "container", None) if LAGOM_AVAILABLE else None
    )
    if container is not None:
        try:
            return container[dependency_type]
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving {dependency_type.__name__} from container",
            )

    # Fallback to app.state

    # Convert class name to `snake_case` for lookup in `app.state`
    state_attr_name = inflection.underscore(dependency_type.__name__)
    dependency_instance = getattr(request.app.state, state_attr_name, None)
    if dependency_instance:
        return cast(T, dependency_instance)

    raise HTTPException(
        status_code=500,
        detail=f"{dependency_type.__name__} not found in Lagom container or app.state",
    )


def get_session_service(request: Request) -> SessionService:
    return resolve_dependency(request, SessionService)


def get_session_store(request: Request) -> SessionStore:
    return resolve_dependency(request, SessionStore)


def get_agent_store(request: Request) -> AgentStore:
    return resolve_dependency(request, AgentStore)


def get_user_store(request: Request) -> UserStore:
    return resolve_dependency(request, UserStore)


def get_event_emitter(request: Request) -> EventEmitter:
    return resolve_dependency(request, EventEmitter)
