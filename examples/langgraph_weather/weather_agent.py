from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    StatusEventData,
)
from flux0_stream.frameworks.langchain import RunContext, filter_and_map_events, handle_event
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from examples.utils.utils import read_user_input


@tool(name_or_callable="get_weather", description="Get the weather for a given city")
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


@agent_runner("langgraph_weather")
class WeatherAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        # read the agent object
        agent = await deps.read_agent(context.agent_id)
        if not agent:
            raise ValueError(f"Agent with id {context.agent_id} not found")
        # read session events and expect the last event to be the user input
        user_input = await read_user_input(deps, context)
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
        try:
            model_events = weather_agent.astream_events(
                input=input,
                config=config,
                version="v2",
            )

            run_ctx: RunContext = RunContext(last_known_event_offset=0)
            # iterate over the model events and stream them to the client
            async for e in filter_and_map_events(model_events, deps.logger):
                await handle_event(
                    agent,
                    deps.correlator.correlation_id,
                    e,
                    deps.event_emitter,
                    deps.logger,
                    run_ctx,
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
