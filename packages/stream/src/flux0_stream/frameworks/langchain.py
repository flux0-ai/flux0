import json
import time
from typing import AsyncIterator, Dict, Optional, cast

from flux0_core.agents import Agent
from flux0_core.logging import Logger
from flux0_core.sessions import TOOL_CALL_PART_TYPE, EventId, StatusEventData
from flux0_core.types import ensure_json_serializable
from langchain_core.messages import AIMessage, ToolMessage, message_chunk_to_message
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables.schema import StreamEvent

from flux0_stream.emitter.api import EventEmitter
from flux0_stream.types import ChunkEvent, JsonPatchOperation


class RunContext:
    def __init__(self, last_known_event_offset: int) -> None:
        self.data: Dict[str, Dict[str, bool]] = {}
        self.last_known_event_offset = last_known_event_offset

    def set_typing_emitted(self, event_id: str, emitted: bool) -> None:
        """Set the typing_emitted status for a given event_id."""
        if event_id not in self.data:
            self.data[event_id] = {}
        self.data[event_id]["typing_emitted"] = emitted

    def get_typing_emitted(self, event_id: str) -> bool:
        """Retrieve the typing_emitted status for a given event_id."""
        return self.data.get(event_id, {}).get("typing_emitted", False)

    def get_last_known_event_offset(self) -> int:
        """Get the last known event offset."""
        return self.last_known_event_offset

    def clear(self) -> None:
        """Clear the entire run context."""
        self.data.clear()
        self.last_known_event_offset = 0  # Reset offset


async def handle_event(
    agent: Agent,
    correlation_id: str,
    event: StreamEvent,
    event_emitter: EventEmitter,
    logger: Logger,
    run_ctx: RunContext,
) -> None:
    if event["event"] == "on_chat_model_start":
        # print("on_chat_model_start :: ", event["run_id"])
        # new chat model execution started

        # TODO do we want meta?
        # chunk = EmittedEvent(
        #     correlation_id=self._correlator.correlation_id,
        #     event_id=event["run_id"],
        #     chunk_id=0,
        #     data="",
        #     is_final=False,
        #     timestamp=time.time(),
        #     metadata={
        #         "provider": meta["ls_provider"],
        #         "model_name": meta["ls_model_name"],
        #         "temperature": meta["ls_temperature"],
        #     },
        # )
        # processing means that the agent is busy with processing the event, this would render a 'thinking...' to the end user
        # NOTE: since currently LLMs 'thinks' a single word ahead it's unlikely that we'll see this status but just in case...
        # (more relevant to tool calls, etc...)
        await event_emitter.enqueue_status_event(
            correlation_id=correlation_id,
            data=StatusEventData(
                type="status",
                acknowledged_offset=run_ctx.get_last_known_event_offset(),
                status="processing",
                data={},
            ),
            event_id=EventId(event["run_id"]),
        )
    elif event["event"] == "on_chat_model_stream":
        run_id = event["run_id"]
        data = event["data"]
        chunk = data.get("chunk", None)
        if not chunk:
            raise ValueError("No chunk in data")
        if not isinstance(chunk, AIMessageChunk):
            raise ValueError("Chunk is not a BaseMessage")
        if not chunk.id:
            raise ValueError("Message has no id")

        msg = message_chunk_to_message(chunk)
        if not isinstance(msg, AIMessage):
            raise ValueError("Message is not an AIMessage")

        # NOTE: for some reason the first event (both when LLM request a tool call and when it produces content) is empty, we can safely ignore it
        # When LLM request a tool call the first chunk is empty followed by a chunk with `tool_calls` key.
        # Ignore empty chunks
        if (
            msg.content == ""
            and not msg.tool_calls
            and not msg.response_metadata.get("finish_reason")
            # this is a tool call chunk, example: (' Francisco' is the chunk of the streamed args)
            # [{'name': None, 'args': ' Francisco', 'id': None, 'error': None, 'type': 'invalid_tool_call'}]
            and not msg.invalid_tool_calls
        ):
            # print("ignore empty chunk")
            return
        # Normal Message Chunk (Switch to Typing)
        if msg.content:
            if not run_ctx.get_typing_emitted(run_id):  # Only emit `typing` once
                await event_emitter.enqueue_status_event(
                    correlation_id=correlation_id,
                    data=StatusEventData(
                        type="status",
                        acknowledged_offset=run_ctx.get_last_known_event_offset(),
                        status="typing",
                        data={},
                    ),
                    event_id=EventId(run_id),
                )
                run_ctx.set_typing_emitted(run_id, True)
            # TODO this is going to work only on strings, we need to handle structs as well
            cec = ChunkEvent(
                correlation_id=correlation_id,
                seq=0,
                event_id=EventId(run_id),
                patches=[
                    {
                        "op": "add",
                        "path": "/-",  # `-` ensures append instead of overwriting
                        "value": ensure_json_serializable(msg.content),
                    }
                ],
                metadata={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                },
                timestamp=time.time(),
            )
            await event_emitter.enqueue_event_chunk(cec)
        if msg.tool_calls:
            # AI requesting a tool call!
            # we have tool_calls and tool_call_chunks, lets try to work always with chunks
            # e.g., [{'name': 'search', 'args': '{"query":"weather in SF"}', 'id': 'call_ej6d', 'index': 0, 'type': 'tool_call_chunk'}]
            # NOTE: patches should construct an object that conforms *ToolCallPart*
            # NOTE this is disabled for now as couldn't find a way to set /tool_calls to [] if it doesn't exist (taken care of right now in _ensure_structure_exists)
            # (1) Ensure /tool_calls exists
            # cec = EventChunk(
            #     correlation_id=correlation_id,
            #     seq=0,
            #     event_id=EventId(run_id),
            #     patches=[
            #         {
            #             "op": "test",
            #             "path": "/tool_calls",
            #             "value": None,
            #         },
            #         {
            #             "op": "add",
            #             "path": "/tool_calls",
            #             "value": [],
            #         },
            #     ],
            #     agent_id=agent.id,
            #     agent_name=agent.name,
            #     timestamp=time.time(),
            #     metadata={},
            # )
            # await event_emitter.enqueue_event_chunk(cec)

            ops: list[JsonPatchOperation] = []
            # (2) Process each tool call chunk
            for tool_call in chunk.tool_call_chunks:
                tool_index = tool_call["index"]
                tool_id = tool_call["id"]
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", None)

                # (3) Ensure tool call entry exists at the correct index
                # NOTE: some chunks may NOT contain all fields, openai mainly returns first the tool_call_id, tool_name and stream args in the next chunks
                # I hope this assumption will hold for all providers where tool_id is always in the first chunk
                if tool_id:
                    ops.append(
                        {
                            "op": "add",
                            "path": f"/tool_calls/{tool_index}",
                            "value": {
                                "type": TOOL_CALL_PART_TYPE,
                                "tool_call_id": tool_id,
                                "tool_name": "",
                                # TODO is it safe for all cases?
                                "args": [],
                            },
                        }
                    )

                # (4) If the tool name is present, update it
                if tool_name:
                    ops.append(
                        {
                            "op": "replace",
                            "path": f"/tool_calls/{tool_index}/tool_name",
                            "value": tool_name,
                        }
                    )

                # (5) If args are received, append them (supporting streaming)
                if tool_args:
                    try:
                        # Check if args is a valid JSON object
                        parsed_args = json.loads(tool_args)
                        # Replace the full args object if it's fully formed
                        ops.append(
                            {
                                "op": "replace",
                                "path": f"/tool_calls/{tool_index}/args",
                                "value": parsed_args,
                            }
                        )
                    except json.JSONDecodeError:
                        # Otherwise, append args as a raw string (for streaming cases)
                        ops.append(
                            {
                                "op": "add",
                                "path": f"/tool_calls/{tool_index}/args/-",
                                "value": tool_args,
                            }
                        )

            cec = ChunkEvent(
                correlation_id=correlation_id,
                seq=0,
                event_id=EventId(run_id),
                patches=ops,
                timestamp=time.time(),
                metadata={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                },
            )
            await event_emitter.enqueue_event_chunk(cec)
        elif msg.invalid_tool_calls:
            for invalid_tool_call in msg.invalid_tool_calls:
                tool_index = msg.additional_kwargs["tool_calls"][0]["index"]
                # at this point we take care only of "args"
                if not invalid_tool_call["args"]:
                    continue
                cec = ChunkEvent(
                    correlation_id=correlation_id,
                    seq=0,
                    event_id=EventId(run_id),
                    patches=[
                        {
                            "op": "add",
                            "path": f"/tool_calls/{tool_index}/args/-",
                            "value": invalid_tool_call["args"],
                        }
                    ],
                    timestamp=time.time(),
                    metadata={
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                    },
                )
                await event_emitter.enqueue_event_chunk(cec)
            pass
        elif msg.response_metadata and msg.response_metadata["finish_reason"] == "tool_calls":
            # print("Tool call request has finished")
            # we could emit ready event here as well but decided to put it on `on_chat_model_end` event
            return
    elif event["event"] == "on_chat_model_end":
        # this means a LLM run ended
        await event_emitter.enqueue_status_event(
            correlation_id=correlation_id,
            data=StatusEventData(
                type="status",
                acknowledged_offset=run_ctx.get_last_known_event_offset(),
                status="ready",
                data={},
            ),
            event_id=EventId(event["run_id"]),
        )
    elif event["event"] == "on_tool_start":
        """
        a tool call has started, we already have an AI message requesting the tool call, not sure how interesting this event is
        event example:
        {
            "event": "on_tool_start",
            "data": {"input": {"query": "weather in sf"}},
            "name": "search",
            "tags": ["seq:step:1"],
            "run_id": "d45b87fe-bcd4-4cdc-942e-7255f27d7e10",
            "metadata": {
                "thread_id": 42,
                "langgraph_step": 2,
                "langgraph_node": "tools",
                "langgraph_triggers": ["branch:agent:should_continue:tools"],
                "langgraph_path": ("__pregel_pull", "tools"),
                "langgraph_checkpoint_ns": "tools:4ce47173-42b8-2d27-a887-de06e13aed5f",
                "checkpoint_ns": "tools:4ce47173-42b8-2d27-a887-de06e13aed5f",
            },
            "parent_ids": [
                "6c1686f3-89b9-49b5-8885-0d42e7957930",
                "aaba85a5-a45c-4539-aaf4-62b35165a0fa",
            ]
        }
        """
        # print("on_tool_start :: ", event["run_id"])
        # new tool execution started
        # await asyncio.sleep(1)
    elif event["event"] == "on_tool_end":
        """
        This event is emitted when a tool call has finished, should emit the output of the tool call here
        {
                "event": "on_tool_end",
                "data": {
                    "output": ToolMessage(
                        content="It's 60 degrees and foggy.",
                        name="search",
                        tool_call_id="call_h67g",
                    ),
                    "input": {"query": "weather in sf"},
                },
                "run_id": "d45b87fe-bcd4-4cdc-942e-7255f27d7e10",
                "name": "search",
                "tags": ["seq:step:1"],
                "metadata": {
                    "thread_id": 42,
                    "langgraph_step": 2,
                    "langgraph_node": "tools",
                    "langgraph_triggers": ["branch:agent:should_continue:tools"],
                    "langgraph_path": ("__pregel_pull", "tools"),
                    "langgraph_checkpoint_ns": "tools:4ce47173-42b8-2d27-a887-de06e13aed5f",
                    "checkpoint_ns": "tools:4ce47173-42b8-2d27-a887-de06e13aed5f",
                },
                "parent_ids": [
                    "6c1686f3-89b9-49b5-8885-0d42e7957930",
                    "aaba85a5-a45c-4539-aaf4-62b35165a0fa",
                ],
        }
        """
        data = event["data"]
        if not data:
            raise ValueError("No data in event")
        output = cast(ToolMessage, data.get("output"))
        patches: list[JsonPatchOperation] = []
        # NOTE: we construct a chunk that looks like ToolEventData, which is actually a list of ToolCall (which looks like ToolCallPart but with result and error)
        # (1) Ensure /tool_calls exists
        patches.append(
            {
                "op": "add",
                "path": "/tool_call_results",
                "value": [],
            }
        )

        # (2) Add the tool call
        patches.append(
            {
                "op": "add",
                "path": "/tool_call_results/-",
                "value": ensure_json_serializable(
                    {
                        "tool_call_id": output.tool_call_id,
                        "tool_name": output.name,
                        "data": {"result": output.content},
                        "args": data.get("input", {}),
                    }
                ),
            }
        )

        await event_emitter.enqueue_event_chunk(
            ChunkEvent(
                correlation_id=correlation_id,
                seq=0,
                event_id=EventId(event["run_id"]),
                patches=patches,
                timestamp=time.time(),
                metadata={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                },
            )
        )

        # Emit event that finalized the tool call (this triggers finalization)
        await event_emitter.enqueue_status_event(
            correlation_id=correlation_id,
            data=StatusEventData(type="status", acknowledged_offset=0, status="ready", data={}),
            event_id=EventId(event["run_id"]),
        )
    else:
        raise ValueError(f"Event {event['event']} not implemented")


async def filter_and_map_events(
    aiter: AsyncIterator[StreamEvent], logger: Logger
) -> AsyncIterator[StreamEvent]:
    root_run_id: Optional[str] = None

    async for event in aiter:
        if event["event"] == "on_chain_start" and not root_run_id:
            root_run_id = event["run_id"]
        elif event["event"] == "on_chain_start":
            pass
        elif event["event"] == "on_chain_stream" and event["run_id"] == root_run_id:
            # note: opengpts take care of this
            pass
        elif event["event"] == "on_chain_stream":
            pass
        elif event["event"] == "on_chat_model_start":
            yield event
        elif event["event"] == "on_chat_model_stream":
            # expecting event to have event["data"]["chunk"] where each chunk should have id and is an AIMessageChunk
            yield event
        elif event["event"] == "on_chat_model_end":
            yield event
        elif event["event"] == "on_chain_end":
            pass
        elif event["event"] == "on_tool_start":
            yield event
        elif event["event"] == "on_tool_end":
            yield event
        elif event["event"] == "on_prompt_start":
            pass
        elif event["event"] == "on_prompt_end":
            pass
        else:
            logger.info(f"Unknown event {event['event']}")
