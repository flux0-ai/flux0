import json
from dataclasses import asdict
from typing import List, Optional, Type, Union

from flux0_stream.types import ChunkEvent, EmittedEvent


def load_events(json_str: str) -> List[Union[EmittedEvent, ChunkEvent]]:
    """
    Load a JSON string containing a list of events and return a list of event objects.
    Each event is converted to either an EmittedEvent (if it has an "id" and "data")
    or a ChunkEvent (if it has "patches").
    """
    data = json.loads(json_str)
    events: List[Union[EmittedEvent, ChunkEvent]] = []
    for event in data:
        event_cls: Optional[Type[Union[EmittedEvent, ChunkEvent]]] = None

        if "id" in event and "data" in event:
            event_cls = EmittedEvent
        elif "patches" in event:
            event_cls = ChunkEvent

        if event_cls is None:
            raise ValueError(f"Unrecognized event format: {event}")

        events.append(event_cls(**event))  # Dynamically instantiate the dataclass

    return events


def dumps_event(event: Union[EmittedEvent, ChunkEvent]) -> str:
    """
    Dump a single event object (EmittedEvent or ChunkEvent) to a JSON string.
    """
    return json.dumps(asdict(event))


def dumps_events(events: List[Union[EmittedEvent, ChunkEvent]]) -> str:
    """
    Dump a list of event objects to a JSON string.
    """
    return json.dumps([asdict(event) for event in events], indent=2)
