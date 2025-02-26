from contextlib import AsyncExitStack
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Mapping, Sequence

import pytest
from flux0_core.agents import Agent, AgentId, AgentType
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import Logger, StdoutLogger
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.emitter.memory import MemoryEventEmitter
from flux0_stream.store.memory import MemoryEventStore
from flux0_stream.types import EmittedEvent


@pytest.fixture
def contextual_correlator() -> ContextualCorrelator:
    return ContextualCorrelator()


@pytest.fixture
def logger(contextual_correlator: ContextualCorrelator) -> Logger:
    return StdoutLogger(correlator=contextual_correlator)


@pytest.fixture
async def event_emitter(logger: Logger) -> AsyncGenerator[EventEmitter, None]:
    """Provide a properly initialized EventEmitter instance using AsyncExitStack for clean resource management."""

    async with AsyncExitStack() as stack:
        store = await stack.enter_async_context(MemoryEventStore())
        emitter = await stack.enter_async_context(
            MemoryEventEmitter(event_store=store, logger=logger)
        )

        yield emitter


@pytest.fixture
async def agent() -> Agent:
    """Provide a test agent instance."""
    return Agent(
        id=AgentId("agent1"),
        name="Agent 1",
        type=AgentType("test_type"),
        description="Test agent",
        created_at=datetime.now(),
    )


def is_subset(small: Any, big: Any) -> bool:
    """Recursively checks if `small` is a subset of `big`, handling nested dicts & lists."""

    if isinstance(small, Mapping) and isinstance(big, Mapping):
        return all(
            key in big and is_subset(small[key], big[key])  # Recurse only if both are mappings
            for key in small
        )

    elif (
        isinstance(small, Sequence)
        and isinstance(big, Sequence)
        and not isinstance(small, (str, bytes))
        and not isinstance(big, (str, bytes))
    ):
        # Ensure every item in `small` is present somewhere in `big`
        return all(any(is_subset(item, big_item) for big_item in big) for item in small)

    else:
        return bool(small == big)


def assert_emitted_event(
    event: EmittedEvent, expected_type: str, expected_data: Dict[str, Any]
) -> None:
    """Helper function to assert event type and check expected data (including nested)."""
    assert event.type == expected_type, f"Expected type '{expected_type}', got '{event.type}'"

    assert is_subset(expected_data, event.data)
