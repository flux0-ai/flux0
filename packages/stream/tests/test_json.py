from typing import List, Union

from flux0_stream.json import dumps_events, load_events
from flux0_stream.types import ChunkEvent, EmittedEvent


def get_sample_events_json() -> str:
    """
    Return a simplified JSON string containing one EmittedEvent and one ChunkEvent.
    """
    return """
    [
      {
        "id": "event-1",
        "source": "ai_agent",
        "type": "status",
        "correlation_id": "sess1",
        "data": {
          "type": "status",
          "status": "processing"
        },
        "metadata": null
      },
      {
        "correlation_id": "sess1",
        "event_id": "event-1",
        "seq": 0,
        "patches": [
          {
            "op": "add",
            "path": "/tool_calls/0",
            "value": {
              "type": "tool_call",
              "tool_call_id": "call-123",
              "tool_name": "",
              "args": []
            }
          }
        ],
        "metadata": { "agent_id": "foo" },
        "timestamp": 1740673638.0
      }
    ]
    """


def test_load_events() -> None:
    sample_json: str = get_sample_events_json()
    events: List[Union[EmittedEvent, ChunkEvent]] = load_events(sample_json)

    # Check that we have exactly 2 events.
    assert len(events) == 2

    # First event should be an EmittedEvent.
    emitted_event = events[0]
    assert isinstance(emitted_event, EmittedEvent)
    assert emitted_event.id == "event-1"
    assert emitted_event.data.get("status") == "processing"

    # Second event should be a ChunkEvent.
    chunk_event = events[1]
    assert isinstance(chunk_event, ChunkEvent)
    assert chunk_event.seq == 0
    assert chunk_event.timestamp == 1740673638.0


def test_dump_events() -> None:
    sample_json: str = get_sample_events_json()
    events: List[Union[EmittedEvent, ChunkEvent]] = load_events(sample_json)

    # Dump events to JSON.
    dumped: str = dumps_events(events)

    # Reload the dumped JSON.
    reloaded_events: List[Union[EmittedEvent, ChunkEvent]] = load_events(dumped)

    # Check that reloading gives us the same events.
    assert events == reloaded_events
