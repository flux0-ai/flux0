import time
import uuid
from dataclasses import dataclass
from datetime import date

from flux0_core.agent_runners.api import Agent as FAgent
from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    EventId,
    StatusEventData,
)
from flux0_stream.emitter.utils.events import send_processing_event
from flux0_stream.types import ChunkEvent
from pydantic_ai import Agent
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.tools import RunContext

from examples.utils.utils import read_user_input


@dataclass
class WeatherService:
    async def get_forecast(self, location: str, forecast_date: date) -> str:
        # In real code: call weather API, DB queries, etc.
        return f"The forecast in {location} on {forecast_date} is 24°C and sunny."

    async def get_historic_weather(self, location: str, forecast_date: date) -> str:
        # In real code: call a historical weather API or DB
        return f"The weather in {location} on {forecast_date} was 18°C and partly cloudy."


weather_agent = Agent[WeatherService, str](
    "openai:gpt-4.1-nano",
    deps_type=WeatherService,
    output_type=str,
    system_prompt="Providing a weather forecast at the locations the user provides.",
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext[WeatherService],
    location: str,
    forecast_date: date,
) -> str:
    if forecast_date >= date.today():
        return await ctx.deps.get_forecast(location, forecast_date)
    else:
        return await ctx.deps.get_historic_weather(location, forecast_date)


async def send_message(
    deps: Deps,
    input: str,
    agent: FAgent,
    event_id: EventId,
):
    await send_processing_event(deps, "thinking...")
    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(input, deps=WeatherService()) as run:
        async for node in run:
            if Agent.is_model_request_node(node):
                # A model request node => We can stream tokens from the model's request
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent):
                            pass
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, TextPartDelta):
                                pass
                            elif isinstance(event.delta, ToolCallPartDelta):
                                pass
                        elif isinstance(event, FinalResultEvent):
                            pass
            elif Agent.is_call_tools_node(node):
                # A handle-response node => The model returned some data, potentially calls a tool
                async with node.stream(run.ctx) as handle_stream:
                    async for event in handle_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            value = f"[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args}"
                            await send_processing_event(deps, value)
                        elif isinstance(event, FunctionToolResultEvent):
                            value = f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}"
                            await send_processing_event(deps, value)
            elif Agent.is_end_node(node):
                assert run.result.output == node.data.output  # type: ignore
                # Once an End node is reached, the agent run is complete
                await deps.event_emitter.enqueue_status_event(
                    correlation_id=deps.correlator.correlation_id,
                    data=StatusEventData(type="status", status="typing"),
                )
                cec = ChunkEvent(
                    correlation_id=deps.correlator.correlation_id,
                    seq=0,
                    event_id=event_id,
                    patches=[
                        {
                            "op": "add",
                            "path": "/-",
                            "value": run.result.output,  # type: ignore
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


@agent_runner("pydantic_weather_agent")
class WeatherAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        try:
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

            await send_message(
                deps=deps,
                input=user_input,
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
