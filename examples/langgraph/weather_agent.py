import time
import uuid
from typing import Any, cast

from flux0_core.agent_runners.api import Agent, AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    EventId,
    StatusEventData,
)
from flux0_stream.types import ChunkEvent
from langchain_core.messages import ToolMessage
from langchain_core.runnables.config import RunnableConfig

from examples.utils.utils import extract_latest_user_input
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

STATUS_EVENT_DATA_KEY = "detail"


async def send_processing_event(deps: Deps, content: str):
    await deps.event_emitter.enqueue_status_event(
        correlation_id=deps.correlator.correlation_id,
        data=StatusEventData(
            type="status", status="processing", data={STATUS_EVENT_DATA_KEY: content}
        ),
    )


async def send_last_msg(
    graph: CompiledStateGraph,
    deps: Deps,
    input: dict[str, Any],
    config: RunnableConfig,
    agent: Agent,
    event_id: EventId,
):
    await send_processing_event(deps, "thinking...")

    it = graph.astream(
        input=input,
        config=config,
        stream_mode=["updates"],
        subgraphs=True,
    )

    current_node_name = None
    new_node_name = None
    value: dict = {}
    while True:
        try:
            chunk = await it.__anext__()
            # key = chunk[0]
            # type = chunk[1]
            value = chunk[2]  # type: ignore
            event_value = ""
            if "tools" in value:
                tool_msg = value["tools"].get("messages")[0]
                tool_msg = cast(ToolMessage, tool_msg)
                new_node_name = tool_msg.name
                event_value = f"called tool: {tool_msg.name}"
            else:
                for node_name in value.keys():
                    deps.logger.info(f"node val: {node_name}")
                    new_node_name = node_name
                    event_value = f"done with: {node_name}"

            if new_node_name != current_node_name:
                await send_processing_event(deps, event_value)
                current_node_name = new_node_name

        except StopAsyncIteration:
            # send last event as message
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="typing"),
            )

            deps.logger.debug(f"Sending last message: {value}")

            current_node_val = value[current_node_name]
            response = (
                current_node_val["response"]
                if "response" in current_node_val
                else current_node_val["messages"][-1].content
            )
            cec = ChunkEvent(
                correlation_id=deps.correlator.correlation_id,
                seq=0,
                event_id=event_id,
                patches=[
                    {
                        "op": "add",
                        "path": "/-",  # `-` ensures append instead of overwriting
                        "value": response,
                    }
                ],
                metadata={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                },
                timestamp=time.time(),
            )
            await deps.event_emitter.enqueue_event_chunk(cec)
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="ready"),
                event_id=event_id,
            )
            break


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


checkpointer = InMemorySaver()
weather_agent = create_react_agent(
    model="gpt-4.1-nano",
    tools=[get_weather],
    prompt="You are a friendly, helpful assistant",
    checkpointer=checkpointer,
)


@agent_runner("langchain_weather_agent")
class WeatherAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        try:
            # read the agent object
            agent = await deps.read_agent(context.agent_id)
            if not agent:
                raise ValueError(f"Agent with id {context.agent_id} not found")

            # read session events and expect the last event to be the user input
            events = await deps.list_session_events(context.session_id)
            user_input = extract_latest_user_input(events)
            if not user_input:
                raise ValueError("No user input found in session events")

            deps.logger.info(
                f"User Input: {user_input} for session {context.session_id} and agent {agent.id}"
            )

            input = {"messages": [("user", user_input)]}
            config = RunnableConfig(
                configurable={
                    "thread_id": context.session_id,
                    "agent_id": agent.id,
                }
            )
            await send_last_msg(
                graph=weather_agent,
                deps=deps,
                input=input,
                config=config,
                agent=agent,
                event_id=EventId(uuid.uuid4().hex),
            )

            return True
        except Exception as e:
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="error", data=str(e)),
            )

            return False
        finally:
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
