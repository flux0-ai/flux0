import asyncio
from pathlib import Path
from typing import AsyncIterator, List, cast

import pytest
from flux0_core.agents import Agent
from flux0_core.logging import Logger
from flux0_core.sessions import StatusEventData
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.frameworks.langchain import (
    RunContext,
    filter_and_map_events,
    handle_event,
)
from flux0_stream.types import ChunkEvent, EmittedEvent
from langchain_core.load import loads
from langchain_core.runnables.schema import StreamEvent
from tests.conftest import assert_emitted_event


async def stream_events_from_file(file_path: Path) -> AsyncIterator[StreamEvent]:
    """Asynchronously stream events from a file."""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                e = loads(line)
                yield e
                # await sleep(0)  # Allows async context switching


@pytest.fixture
def langchain_events(request: pytest.FixtureRequest) -> AsyncIterator[StreamEvent]:
    file_path = (
        Path(request.node.fspath).parent / "../" / "fixtures" / "langchain_search_tool_astream.json"
    )
    return stream_events_from_file(file_path)


@pytest.mark.asyncio
async def test_langchain_streaming(
    logger: Logger,
    agent: Agent,
    event_emitter: EventEmitter,
    langchain_events: AsyncIterator[StreamEvent],
) -> None:
    # Subscribe to final events.
    final_events: List[EmittedEvent] = []

    async def final_subscriber(final_event: EmittedEvent) -> None:
        if final_event.type == "status":
            data = cast(StatusEventData, final_event.data)
            if data["status"] == "typing":
                return

        final_events.append(final_event)

    async def processed_subscriber(event_chunk: ChunkEvent) -> None:
        # TODO test
        ...

    correlation_id = "test_corr_langchain"
    event_emitter.subscribe_final(correlation_id, final_subscriber)
    event_emitter.subscribe_processed(correlation_id, processed_subscriber)

    run_ctx = RunContext(last_known_event_offset=0)
    async for event in filter_and_map_events(langchain_events, logger):
        await handle_event(
            agent=agent,
            correlation_id=correlation_id,
            logger=logger,
            event=event,
            event_emitter=event_emitter,
            run_ctx=run_ctx,
        )
    # yield control to the event loop to allow async processing
    await asyncio.sleep(0)
    assert len(final_events) > 3

    # # (1st) is always processing
    assert_emitted_event(
        final_events[0], expected_type="status", expected_data={"status": "processing"}
    )

    # # (2nd) is LLM requesting a tool call
    assert_emitted_event(
        final_events[1],
        expected_type="message",
        expected_data={
            # "type": "tool_call",
            # "tool_name": "search",
            "parts": [
                {
                    "args": {"query": "San Francisco weather"},
                }
            ]
        },
    )

    # (3rd) is the tool call response
    assert_emitted_event(
        final_events[2],
        expected_type="tool",
        expected_data={
            "type": "tool_call_result",
            "tool_calls": [
                {
                    "tool_name": "search",
                    "args": {"query": "San Francisco weather"},
                    "result": {"data": "It's 60 degrees and foggy."},
                }
            ],
        },
    )

    # (4th) LLM is processing a new message
    assert_emitted_event(
        final_events[3], expected_type="status", expected_data={"status": "processing"}
    )

    # (5th) LLM generated a message once received the tool call result
    assert_emitted_event(
        final_events[4],
        expected_type="message",
        expected_data={
            "parts": [
                {
                    "type": "content",
                    "content": "The weather in San Francisco is currently 60 degrees and foggy.",
                }
            ]
        },
    )
