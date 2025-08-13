import asyncio
import time
import uuid

from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    EventId,
    StatusEventData,
)
from flux0_stream.types import ChunkEvent

from examples.utils.utils import read_user_input, send_processing_event


@agent_runner("static_agent")
class StaticAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        # read the agent object
        agent = await deps.read_agent(context.agent_id)
        if not agent:
            raise ValueError(f"Agent with id {context.agent_id} not found")

        # read session events and extract user input
        user_input = await read_user_input(deps, context)
        if not user_input:
            raise ValueError("No user input found in session events")
        deps.logger.info(
            f"User Input: {user_input} for session {context.session_id} and agent {agent.id}"
        )

        # TODO: a workaround for https://github.com/flux0-ai/flux0/issues/91
        await asyncio.sleep(2)
        # send processing event, indicating that the agent is thinking
        await send_processing_event(deps, "Thinking...")
        await asyncio.sleep(2)
        await send_processing_event(deps, "Reasoning...")

        # create a chunk event to send a tool call
        event_id = EventId(uuid.uuid4().hex)
        tool_call = ChunkEvent(
            correlation_id=deps.correlator.correlation_id,
            seq=0,
            event_id=event_id,
            patches=[
                {
                    "op": "add",
                    "path": "/tool_calls/0",
                    "value": {
                        "type": "tool_call",
                        "tool_call_id": "id1234",
                        "tool_name": "get_weather",
                        "args": {"city": "tel aviv"},
                    },
                }
            ],
            timestamp=time.time(),
            metadata={
                "agent_id": agent.id,
                "agent_name": agent.name,
            },
        )
        await deps.event_emitter.enqueue_event_chunk(tool_call)
        # send status events to indicate the agent is ready to process more, this completes the tool call run as tool calls may be chunked
        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(type="status", status="ready"),
            event_id=event_id,
        )

        # simulate a delay of a tool call
        await asyncio.sleep(1)

        # create and enqueue tool call result event
        event_id = EventId(uuid.uuid4().hex)
        tool_call_result = ChunkEvent(
            correlation_id=deps.correlator.correlation_id,
            seq=0,
            event_id=event_id,
            patches=[
                {
                    "op": "add",
                    "path": "/tool_call_results/0",
                    "value": {
                        "tool_call_id": "id1234",
                        "tool_name": "get_weather",
                        "data": {"result": "It's always sunny in Israel!"},
                        "args": {"city": "tel aviv"},
                    },
                }
            ],
            timestamp=time.time(),
            metadata={
                "agent_id": agent.id,
                "agent_name": agent.name,
            },
        )

        await deps.event_emitter.enqueue_event_chunk(tool_call_result)
        # send status events to complete the tool call run and indicate the agent is ready to process more
        await deps.event_emitter.enqueue_status_event(
            correlation_id=deps.correlator.correlation_id,
            data=StatusEventData(type="status", status="ready"),
            event_id=event_id,
        )

        # enqueue a typing status event to indicate the agent is typing
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
            # event_id=event_id,
        )

        # the run was successful
        return True
