import asyncio
import contextvars
import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import IntEnum, auto
from typing import Any, Dict, Iterator, Optional, override

import structlog
from structlog.types import EventDict
from structlog.typing import Processor

from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.ids import gen_id


class LogLevel(IntEnum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    def logging_level(self) -> int:
        return {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }[self]


class Logger(ABC):
    """
    Logging interface for structured logs with support for scopes and operation measurement.
    """

    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        ...

    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    @contextmanager
    def scope(self, scope_id: str) -> Iterator[None]:
        """
        Create a new logging scope. Any log issued within this context
        will include the provided scope id.
        """
        ...

    @abstractmethod
    @contextmanager
    def operation(self, name: str, props: Optional[Dict[str, Any]] = None) -> Iterator[None]:
        """
        Context manager that logs the start and end of an operation.
        Measures execution time and handles cancellations/exceptions.
        """
        ...


class ContextualLogger(Logger):
    """
    A structured logger with support for correlation and scopes.

    Correlation links related logs across systems that are part of the same context (e.g., HTTP Request), while scope provides finer-grained tracking within a process."

    What is Corrleation?
    Correlation refers to a unique identifier (correlation ID) that links related logs together across different services.
    Useful for tracking a request end-to-end across microservices, threads, or async tasks.
    Typically, a correlation ID remains the same across multiple logs that are part of the same "request" (e.g., HTTP request), "session" or "transaction."

    Example of Correlation:
    When a user makes an HTTP request, we generate a correlation ID and attach it to all logs where multiple services
    handle this request should log with the same correlation ID.
    {
        "timestamp": "2025-02-26T10:41:37.917Z",
        "level": "info",
        "event": "User login request received",
        "correlation_id": "request-12345"
    }


    What is scope?
    Scope is more granular and refers to a specific context within a process.
    Scopes allow to track sub-operations within a correlated request.
    Each scope is added on top of the existing correlation ID, making logs more informative.
    Example of Scope:
    A user logs in (correlation_id: request-12345):
    {
        "timestamp": "2025-02-26T10:42:10.917Z",
        "level": "info",
        "event": "Querying user data",
        "correlation_id": "request-12345",
        "scope": "[UserLogin]"
    }

    How Are They Used Together?
    (1) A user logs in → Generate a correlation ID
    with correlator.scope("UserLogin"):
        logger.info("User login request received")
    log output:
    {
      ...
      "correlation_id": "request-12345",
      "scope": "[UserLogin]"
    }

    (2) Inside the login request, we fetch user details → Add a scope
    with logger.scope("FetchUser"):
        logger.info("Fetching user details from DB")
    log output:
    {
      ...
      "correlation_id": "request-12345",
      "scope": "[UserLogin][FetchUser]"
    }

    (3) Validate credentials → Add a scope
    with logger.scope("ValidateCredentials"):
        logger.info("Validating user credentials")
    log output:
    {
      ...
      "correlation_id": "request-12345",
      "scope": "[UserLogin][FetchUser][ValidateCredentials]"
    }
    """

    def __init__(
        self,
        correlator: ContextualCorrelator,
        level: LogLevel = LogLevel.DEBUG,
        logger_id: str | None = None,
        renderer: Optional[Processor] = None,
    ) -> None:
        self.correlator = correlator
        # Context variable for additional logging scopes.
        self._instance_id = gen_id()
        self._scopes: contextvars.ContextVar[str] = contextvars.ContextVar(
            f"logger_{self._instance_id}_scopes", default=""
        )
        self.raw_logger = logging.getLogger(logger_id or "flux0")
        self.raw_logger.setLevel(level.logging_level())

        def add_context_fields(_: "ContextualLogger", __: str, event_dict: EventDict) -> EventDict:
            """
            Processor to inject correlation_id and scope_id into the structured log.
            Since structlog does not pass our StructuredLogger instance, we retrieve the values from context.
            """
            event_dict["correlation"] = self.correlator.correlation_id
            if self._scopes.get():
                event_dict["scope"] = self._scopes.get()
            return event_dict

        # Use JSONRenderer by default unless another renderer is provided.
        renderer = renderer if renderer is not None else structlog.processors.JSONRenderer()

        # Wrap raw_logger with structlog to support structured logging.
        self._logger = structlog.wrap_logger(
            self.raw_logger,
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.stdlib.filter_by_level,
                add_context_fields,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                renderer,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )

    @override
    def set_level(self, level: LogLevel) -> None:
        self.raw_logger.setLevel(level.logging_level())

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(self._format_message(message), *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(self._format_message(message), *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(self._format_message(message), *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._format_message(message), *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(self._format_message(message), *args, **kwargs)

    @contextmanager
    def scope(self, scope_id: str) -> Iterator[None]:
        """
        Extend the logging scope with an additional identifier.
        """
        current_scope = self._scopes.get()
        new_scope = f"{current_scope}[{scope_id}]" if current_scope else f"[{scope_id}]"
        token = self._scopes.set(new_scope)
        try:
            yield
        finally:
            self._scopes.reset(token)

    @property
    def current_scope(self) -> str:
        return self._scopes.get() if self._scopes.get() else ""

    @contextmanager
    def operation(self, name: str, props: Optional[Dict[str, Any]] = None) -> Iterator[None]:
        """
        Context manager that logs the beginning and end of an operation,
        including timing and error handling.
        """
        props = props or {}
        start_time = time.time()
        self.info(f"{name} started", **props)
        try:
            yield
            elapsed = time.time() - start_time
            self.info(f"{name} completed in {elapsed:.3f}s", **props)
        except asyncio.CancelledError:
            elapsed = time.time() - start_time
            self.warning(f"{name} cancelled after {elapsed:.3f}s", **props)
            raise
        except Exception:
            self.error(f"{name} failed", **props)
            self.error("Exception details", exc_info=True)
            raise

    def _format_message(self, message: str) -> str:
        """
        Prepend the current correlation id and scope information to the message.
        """
        correlation = self.correlator.correlation_id
        return f"[{correlation}]{self.current_scope} {message}"


class StdoutLogger(ContextualLogger):
    def __init__(
        self,
        correlator: ContextualCorrelator,
        log_level: LogLevel = LogLevel.DEBUG,
        logger_id: str | None = None,
        json: bool = True,
    ) -> None:
        super().__init__(
            correlator,
            log_level,
            logger_id,
            structlog.dev.ConsoleRenderer(colors=True) if not json else None,
        )
        self.raw_logger.addHandler(logging.StreamHandler())
