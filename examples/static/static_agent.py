import asyncio
import time
import uuid
from typing import cast

from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    EventId,
    MessageEventData,
    StatusEventData,
)
from flux0_stream.types import ChunkEvent


@agent_runner("static_agent")
class StaticAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        # read the agent object
        agent = await deps.read_agent(context.agent_id)
        if not agent:
            raise ValueError(f"Agent with id {context.agent_id} not found")

        # read session events and expect the last event to be the user input
        events = await deps.list_session_events(context.session_id)
        last_event = events[-1]
        if last_event.type != "message":
            return False
        user_event_data = cast(MessageEventData, last_event.data)
        for part in user_event_data["parts"]:
            if part["type"] == "content":
                user_input = part["content"]
                break
        if not user_input:
            raise ValueError("No TextPart found in user event data")

        deps.logger.info(
            f"User Input: {user_input} for session {context.session_id} and agent {agent.id}"
        )

        # send processing event, indicating that the agent is thinking
        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(
                type="status",
                status="processing",
                # optionally include a detailed processing message
                data={"detail": "Thinking...!"},
            ),
        )
        await asyncio.sleep(1.5)

        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(type="status", status="typing"),
        )
        # create a chunk event to send a response, we can stream multiple chunks for the same event id
        event_id = EventId(uuid.uuid4().hex)
        cec = ChunkEvent(
            correlation_id=deps.correlator.correlation_id,
            seq=0,
            event_id=event_id,
            patches=[
                {
                    "op": "add",
                    "path": "/-",  # `-` ensures append instead of overwriting
                    "value": f"Hey there! I received your input: {user_input}",
                }
            ],
            metadata={
                "agent_id": agent.id,
                "agent_name": agent.name,
            },
            timestamp=time.time(),
        )
        print(f"Sending response: {cec}")
        await deps.event_emitter.enqueue_event_chunk(cec)

        # send status events to indicate the agent is ready to process more
        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(type="status", status="ready"),
            event_id=event_id,
        )

        # send a final status event to indicate the run is completed
        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(type="status", status="completed"),
            event_id=event_id,
        )

        # the run was successful
        return True
