from typing import cast

from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import (
    MessageEventData,
    StatusEventData,
)
from flux0_stream.frameworks.langchain import RunContext, filter_and_map_events, handle_event
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage


async def read_user_input(deps: Deps, context: Context) -> str:
    """Extract user input from the last message event."""
    # read session events and expect the last event to be the user input
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


@agent_runner("langchain_simple")
class LangChainAgentRunner(AgentRunner):
    async def run(self, context: Context, deps: Deps) -> bool:
        # Read the agent model from db
        agent = await deps.read_agent(context.agent_id)
        if not agent:
            deps.logger.error(f"Agent with ID {context.agent_id} not found")
            return False

        user_input = await read_user_input(deps, context)

        # initialize and run the chat model via LangChain in streaming mode
        model = init_chat_model("gpt-4.1-nano", model_provider="openai")
        messages = [
            SystemMessage("Translate the following from English into Italian"),
            HumanMessage(user_input),
        ]
        try:
            model_events = model.astream_events(
                messages,
                stream=True,
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
        except Exception as e:
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="error", data=str(e)),
            )
            return False
        finally:
            # mark session stream completion
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed", acknowledged_offset=0),
            )

        return True
