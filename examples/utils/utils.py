from typing import cast

from flux0_core.agent_runners.api import Deps
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import MessageEventData


async def read_user_input(deps: Deps, context: Context) -> str:
    """Extract user input from the last message event."""

    # read session events and expect the last event to be the user input
    user_input = None

    events = await deps.list_session_events(context.session_id)
    last_event = events[-1]
    if last_event.type != "message":
        raise ValueError(f"Expected last event to be a message, got {last_event.type}")
    user_event_data = cast(MessageEventData, last_event.data)
    for part in user_event_data["parts"]:
        if part["type"] == "content":
            user_input = part["content"]
            break
    if not user_input:
        raise ValueError("No TextPart found in user event data")

    return str(user_input)
