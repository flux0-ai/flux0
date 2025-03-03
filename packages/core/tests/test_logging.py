import asyncio
import json
import logging
import time
from typing import Any, Dict, List

import pytest
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import ContextualLogger, Logger, LogLevel


# -----------------------------------------------------------------------------
# Custom In-Memory Log Handler for Testing
# -----------------------------------------------------------------------------
class ListHandler(logging.Handler):
    """Custom log handler that stores log records in a list for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.records: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store structured log data correctly as dictionaries."""
        log_entry = self.format(record)
        try:
            parsed_entry = json.loads(log_entry)  # Correctly parse JSON logs
            self.records.append(parsed_entry)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse log entry as JSON: {log_entry}")


# -----------------------------------------------------------------------------
# Pytest Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def contextual_correlator() -> ContextualCorrelator:
    """Provides a fresh instance of ContextualCorrelator for each test."""
    return ContextualCorrelator()


@pytest.fixture
def logger(contextual_correlator: ContextualCorrelator) -> Logger:
    """Provides a fresh StructuredLogger with a ListHandler for capturing logs."""
    log = ContextualLogger(contextual_correlator, level=LogLevel.DEBUG)
    list_handler = ListHandler()
    list_handler.setFormatter(logging.Formatter("%(message)s"))
    log.raw_logger.addHandler(list_handler)
    log.raw_logger.propagate = False  # Prevent propagation to root logger
    return log


@pytest.fixture
def list_handler(logger: ContextualLogger) -> ListHandler:
    """Provides access to the ListHandler attached to the logger."""
    handler = next(h for h in logger.raw_logger.handlers if isinstance(h, ListHandler))
    assert isinstance(handler, ListHandler)
    handler.records.clear()
    return handler


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_default_correlation(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure the default correlation ID is included in structured logs."""
    logger.info("Test default correlation")

    assert len(list_handler.records) > 0, "No log records captured."
    log_entry = list_handler.records[0]

    assert log_entry["correlation"] == "<main>", "Default correlation ID missing in structured log."


def test_correlation_scope(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure correlation scopes correctly modify structured log fields."""
    with logger.scope("TestScope"):
        logger.info("Scoped correlation test")

    assert len(list_handler.records) > 0, "No log records captured."
    log_entry = list_handler.records[0]

    assert log_entry["correlation"] == "<main>", (
        "Correlation not properly injected into event_dict."
    )

    assert log_entry["scope"] == "[TestScope]", "Scope not properly injected into event_dict."


def test_logger_scope(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure logger.scope() correctly modifies structured log fields."""
    logger.info("Before scope")

    with logger.scope("Inner"):
        logger.info("Inside scope")

    logger.info("After scope")

    before_scope_entry = list_handler.records[0]
    inside_scope_entry = list_handler.records[1]
    after_scope_entry = list_handler.records[2]

    assert "scope" not in before_scope_entry, "Logger scope should not exist before entering."
    assert inside_scope_entry.get("scope") == "[Inner]", "Logger scope '[Inner]' missing."
    assert "scope" not in after_scope_entry, "Logger scope should not persist outside."


def test_operation_success(logger: Logger, list_handler: ListHandler) -> None:
    """Verify logging of operation start and finish messages."""
    with logger.operation("OpSuccess", {"key": "value"}):
        time.sleep(0.1)

    assert len(list_handler.records) >= 2, "Operation start/finish logs missing."

    start_log = list_handler.records[0]
    end_log = list_handler.records[1]

    assert start_log["event"] == "[<main>] OpSuccess started", "Operation start message incorrect."
    assert end_log["event"].startswith("[<main>] OpSuccess completed in"), (
        "Operation completed message incorrect."
    )


def test_operation_exception(logger: Logger, list_handler: ListHandler) -> None:
    """Verify logging of failed operations with structured exceptions."""
    with pytest.raises(ValueError):
        with logger.operation("OpFail", {"error": "test"}):
            raise ValueError("Test exception")

    assert len(list_handler.records) >= 2, "Failed operation logs missing."

    error_log = list_handler.records[-2]
    exception_log = list_handler.records[-1]

    assert error_log["event"] == "[<main>] OpFail failed", "Operation failure not logged correctly."
    assert "exception" in exception_log, "Exception details missing"


def test_operation_cancelled(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure cancelled operations are logged correctly."""
    with pytest.raises(asyncio.CancelledError):
        with logger.operation("OpCancelled"):
            raise asyncio.CancelledError()

    assert len(list_handler.records) >= 2, "Cancelled operation logs missing."

    cancelled_log = list_handler.records[-1]

    assert "OpCancelled cancelled after" in cancelled_log["event"], (
        "Cancelled operation log message incorrect."
    )


def test_structured_log_output(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure logs are fully structured and contain key-value pairs."""
    logger.info("Structured test", user="john_doe", action="login")

    assert len(list_handler.records) > 0, "No log records captured."

    log_entry = list_handler.records[0]

    assert log_entry["event"] == "[<main>] Structured test", "Log event incorrect."
    assert log_entry["user"] == "john_doe", "User field missing in structured log."
    assert log_entry["action"] == "login", "Action field missing in structured log."
    assert "timestamp" in log_entry, "Timestamp missing from structured log."
    assert "level" in log_entry, "Log level missing from structured log."


def test_nested_correlation_scope(
    contextual_correlator: ContextualCorrelator, logger: Logger, list_handler: ListHandler
) -> None:
    """Ensure nested correlation scopes concatenate correctly."""

    with contextual_correlator.scope("user:123"):
        logger.info("User context log")

        with contextual_correlator.scope("session:456"):
            logger.info("Session context log")

            with contextual_correlator.scope("action:update-profile"):
                logger.info("Action context log")

    # Validate that all logs captured the expected correlation scope
    assert len(list_handler.records) >= 3, "Not all nested logs were captured."

    assert list_handler.records[0]["correlation"] == "user:123"
    assert list_handler.records[1]["correlation"] == "user:123::session:456"
    assert list_handler.records[2]["correlation"] == "user:123::session:456::action:update-profile"


def test_nested_logger_scope(logger: Logger, list_handler: ListHandler) -> None:
    """Ensure nested logger scopes concatenate correctly."""

    logger.info("Before nested scope")

    with logger.scope("outer"):
        logger.info("Inside outer scope")

        with logger.scope("inner"):
            logger.info("Inside inner scope")

        logger.info("After inner scope")

    logger.info("After outer scope")

    # Validate that all logs captured the expected logger scope
    assert len(list_handler.records) >= 5, "Not all nested logs were captured."

    assert "scope" not in list_handler.records[0]
    assert list_handler.records[1]["scope"] == "[outer]"
    assert list_handler.records[2]["scope"] == "[outer][inner]"
    assert list_handler.records[3]["scope"] == "[outer]"
    assert "scope" not in list_handler.records[4]


def test_nested_correlation_scopes_and_logger_scopes(
    contextual_correlator: ContextualCorrelator, logger: Logger, list_handler: ListHandler
) -> None:
    """Ensure nested correlation scopes and logger scopes concatenate correctly."""

    with contextual_correlator.scope("user:123"):
        logger.info("User context log")

        with logger.scope("outer"):
            logger.info("Before nested correlation scope")

            with contextual_correlator.scope("session:456"):
                logger.info("Session context log")

                with logger.scope("inner"):
                    logger.info("Inside nested correlation scope")

                    with contextual_correlator.scope("action:update-profile"):
                        logger.info("Action context log")

                        with logger.scope("innermost"):
                            logger.info("Inside innermost correlation scope")

                    logger.info("After innermost correlation scope")

                logger.info("After nested correlation scope")

            logger.info("After outer correlation scope")

        logger.info("After user context log")

    # Validate that all logs captured the expected logger scope and correlation
    assert len(list_handler.records) >= 7, "Not all nested logs were captured."

    assert list_handler.records[0]["correlation"] == "user:123"
    assert "scope" not in list_handler.records[0]

    assert list_handler.records[1]["correlation"] == "user:123"
    assert list_handler.records[1]["scope"] == "[outer]"

    assert list_handler.records[2]["correlation"] == "user:123::session:456"
    assert list_handler.records[2]["scope"] == "[outer]"

    assert list_handler.records[3]["correlation"] == "user:123::session:456"
    assert list_handler.records[3]["scope"] == "[outer][inner]"

    assert list_handler.records[4]["correlation"] == "user:123::session:456::action:update-profile"
    assert list_handler.records[4]["scope"] == "[outer][inner]"

    assert list_handler.records[5]["correlation"] == "user:123::session:456::action:update-profile"
    assert list_handler.records[5]["scope"] == "[outer][inner][innermost]"

    assert list_handler.records[6]["correlation"] == "user:123::session:456"
    assert list_handler.records[6]["scope"] == "[outer][inner]"
