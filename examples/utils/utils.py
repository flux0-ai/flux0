from typing import Optional, Sequence, cast

from flux0_core.sessions import Event, MessageEventData


def extract_user_input_from_events(events: Sequence[Event]) -> Optional[str]:
    """
    Extract user input from a list of session events.

    This function looks for the last message event in the events list
    and extracts the text content from its parts.

    Args:
        events: List of session events

    Returns:
        The user input text if found, None otherwise

    Raises:
        ValueError: If the last event is not a message event or no content part is found
    """
    if not events:
        return None

    last_event = events[-1]
    if last_event.type != "message":
        raise ValueError("Last event is not a message event")

    user_event_data = cast(MessageEventData, last_event.data)

    for part in user_event_data["parts"]:
        if part["type"] == "content":
            content = part["content"]
            if isinstance(content, str):
                return content

    raise ValueError("No content part found in user event data")


def extract_latest_user_input(events: Sequence[Event]) -> Optional[str]:
    """
    Extract the latest user input from session events, returning None if not found
    instead of raising an exception.

    Args:
        events: List of session events

    Returns:
        The user input text if found, None otherwise
    """
    try:
        return extract_user_input_from_events(events)
    except (ValueError, IndexError):
        return None
