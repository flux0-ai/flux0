# openai_chat.py

import asyncio
import time
import uuid
from typing import cast

from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.sessions import EventId, MessageEventData, StatusEventData
from flux0_stream.types import ChunkEvent, JsonPatchOperation
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam


@agent_runner("openai_simple")
class OpenAIChatAgentRunner(AgentRunner):
    def __init__(self) -> None:
        self.client: AsyncOpenAI = AsyncOpenAI()  # Uses env OPENAI_API_KEY

    async def run(self, context: Context, deps: Deps) -> bool:
        agent = await deps.read_agent(context.agent_id)
        if not agent:
            raise ValueError(f"Agent {context.agent_id} not found")

        # Get user input
        events = await deps.list_session_events(context.session_id)
        last_event = events[-1]
        if last_event.type != "message":
            return False

        user_event_data = cast(MessageEventData, last_event.data)
        user_input = next(
            (part["content"] for part in user_event_data["parts"] if part["type"] == "content"),
            None,
        )
        if not user_input:
            raise ValueError("No user input content found")

        event_id = EventId(uuid.uuid4().hex)
        seq = 0

        try:
            # Emit initial processing + typing statuses
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(
                    type="status", status="processing", data={"detail": "Thinking..."}
                ),
            )
            await asyncio.sleep(0.5)

            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="typing"),
            )

            messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content="Be concise."),
                ChatCompletionUserMessageParam(role="user", content=str(user_input)),
            ]
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                stream=True,
                messages=messages,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    patch: JsonPatchOperation = {
                        "op": "add",
                        "path": "/-",
                        "value": delta,
                    }
                    chunk_event = ChunkEvent(
                        correlation_id=deps.correlator.correlation_id,
                        seq=seq,
                        event_id=event_id,
                        patches=[patch],
                        metadata={"agent_id": agent.id, "agent_name": agent.name},
                        timestamp=time.time(),
                    )
                    await deps.event_emitter.enqueue_event_chunk(chunk_event)
                    seq += 1

            # Send 'ready' when done
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                event_id=event_id,
                data=StatusEventData(type="status", status="ready"),
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
                data=StatusEventData(
                    type="status",
                    status="completed",
                    acknowledged_offset=0,
                ),
            )
