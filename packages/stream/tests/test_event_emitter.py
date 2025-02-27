import asyncio
import time

import pytest
from flux0_core.sessions import EventId
from flux0_stream.emitter.api import EventEmitter
from flux0_stream.types import AddOperation, ChunkEvent

# NOTE:
# The following fixture is expected to be provided by test configuration (e.g. via conftest.py).
# It must return an instance of EventEmitter independent of its underlying implementation.
#
# e.g., conftest.py might have:
#
#   @pytest.fixture
#   async def event_emitter() -> EventEmitter:
#       from flux0_stream.store.memory import InMemoryEventStore
#       from flux0_stream.emitter.memory import InMemoryEventEmitter
#
#       store = InMemoryEventStore()
#       emitter = InMemoryEventEmitter(event_store=store)
#       yield emitter
#       await emitter.shutdown()
#


# ------------------------------------------------------------------------------
# Test that a processed subscriber is called when an event chunk is enqueued.
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_processed_subscriber_called_on_event_chunk(
    event_emitter: EventEmitter,
) -> None:
    received_chunks: list[ChunkEvent] = []

    async def processed_subscriber(chunk: ChunkEvent) -> None:
        received_chunks.append(chunk)

    correlation_id = "test_corr_processed"
    event_emitter.subscribe_processed(correlation_id, processed_subscriber)
    # Create an EventChunk that uses a patch operation with an append (indicated by path ending with "/-")
    patch: AddOperation = AddOperation(op="add", path="/age", value=30)
    chunk = ChunkEvent(
        correlation_id=correlation_id,
        event_id=EventId("event1"),
        seq=0,
        patches=[patch],
        metadata={},
        timestamp=time.time(),
    )

    await event_emitter.enqueue_event_chunk(chunk)
    await asyncio.sleep(0.01)  # Allow some time for async processing

    assert len(received_chunks) == 1
    assert received_chunks[0] == chunk
