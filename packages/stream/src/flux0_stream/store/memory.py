import copy
import json
from typing import Dict, List, MutableMapping, Optional, Self, TypedDict, Union, cast

from flux0_core.agents import AgentId
from flux0_core.sessions import (
    ContentPart,
    EventId,
    MessageEventData,
    Participant,
    ReasoningPart,
    ToolCall,
    ToolCallPart,
    ToolCallPartType,
    ToolEventData,
    ToolResult,
)
from flux0_core.types import JSONSerializable
from flux0_stream.patches import ensure_structure_for_patch
from flux0_stream.store.api import EventStore
from flux0_stream.types import ChunkEvent, EmittedEvent
from jsonpatch import JsonPatch, apply_patch


# consider moving this to types if it makes sense for other implementations
class DocInProgress(TypedDict, total=False):
    metadata: MutableMapping[str, JSONSerializable]
    content: JSONSerializable


class MemoryEventStore(EventStore):
    """
    In-memory implementation of EventStore.
    - Applies JSON patches incrementally.
    - Handles out-of-order chunk arrivals using sequence numbers.
    - Finalization is instant, as the document is always up-to-date.
    """

    def __init__(self) -> None:
        # Store in-progress documents
        self.in_progress_docs: Dict[EventId, DocInProgress] = {}
        # Store received patches that arrived out of order
        self.chunk_buffer: Dict[EventId, Dict[int, List[JsonPatch]]] = {}
        # Track the last successfully applied chunk index
        self.chunk_index_tracker: Dict[EventId, int] = {}
        # Store finalized events
        self.finalized_events: Dict[EventId, EmittedEvent] = {}

    async def __aenter__(self) -> Self:
        """Allows the event store to be used with an async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[object],
    ) -> None:
        # """Ensures the event store is properly cleaned up when used in an async context manager."""
        self.in_progress_docs.clear()
        self.chunk_buffer.clear()
        self.chunk_index_tracker.clear()
        self.finalized_events.clear

    async def add_chunk(self, chunk: ChunkEvent) -> None:
        """
        Receives a patch chunk and applies it immediately if it's in order.
        If out of order, stores it in a buffer for later application.
        """
        event_id = chunk.event_id

        # ensure event doc exists
        if event_id not in self.in_progress_docs:
            self.in_progress_docs[event_id] = DocInProgress(
                metadata={
                    **chunk.metadata,
                },
            )

        sequence_number = chunk.seq
        expected_index = self.chunk_index_tracker.get(event_id, -1) + 1

        # apply_patch modifies the patch object
        jpatch_copy = copy.deepcopy(chunk.patches)
        # convert raw operations to JsonPatch object
        jpatch = JsonPatch(jpatch_copy)

        # ensure the document has the expected structure before applying patches
        doc_in_progress = self.in_progress_docs[event_id]

        # contains_append = any(op["path"].endswith("/-") for op in patch_obj.patch
        contains_append = any(op["path"].endswith("/-") for op in jpatch.patch)

        if contains_append or sequence_number == expected_index:
            # ✅ Apply patch immediately (correct order or append mode)
            doc_in_progress = self.in_progress_docs[event_id]
            for patch in jpatch:
                content = ensure_structure_for_patch(doc_in_progress.get("content"), patch)
                # should never happen coz we are ensuring the structure
                content = apply_patch(content, [patch])
                if content is None:
                    raise ValueError("Document content is missing")
                doc_in_progress["content"] = content
            self.chunk_index_tracker[event_id] = sequence_number
            self.in_progress_docs[event_id] = doc_in_progress

            # 🔄 **Check if we can now apply buffered patches (fill gaps)**
            self._apply_buffered_patches(event_id)
        else:
            # ❌ Out-of-order chunk, store in buffer
            if sequence_number not in self.chunk_buffer[event_id]:
                self.chunk_buffer[event_id][sequence_number] = []
            self.chunk_buffer[event_id][sequence_number].append(jpatch)

    def _apply_buffered_patches(self, event_id: EventId) -> None:
        """Applies buffered patches when their missing previous chunks arrive."""
        # Ensure buffer exists before accessing it
        if event_id not in self.chunk_buffer:
            return  # Nothing to apply

        while self.chunk_index_tracker[event_id] + 1 in self.chunk_buffer.get(event_id, {}):
            next_index = self.chunk_index_tracker[event_id] + 1
            patches_to_apply = self.chunk_buffer[event_id].pop(next_index)

            for patch in patches_to_apply:
                self.in_progress_docs[event_id] = apply_patch(
                    self.in_progress_docs[event_id], patch
                )

            self.chunk_index_tracker[event_id] = next_index  # Update latest index

        # Cleanup: If no more buffered patches, remove entry from chunk_buffer
        if not self.chunk_buffer[event_id]:
            del self.chunk_buffer[event_id]

    async def finalize_event(
        self, correlation_id: str, event_id: EventId
    ) -> Optional[EmittedEvent]:
        """
        Finalizes an event by returning the fully built document.
        Removes it from the in-progress store and marks it as finalized.
        """
        if event_id not in self.in_progress_docs:
            return None  # No document found

        final_data = self.in_progress_docs.pop(event_id)
        self.chunk_buffer.pop(event_id, None)  # Cleanup buffered patches
        self.chunk_index_tracker.pop(event_id, None)  # Cleanup tracking

        meta = final_data.get("metadata", {})
        content = final_data.get("content")
        agent_id = AgentId(str(meta.pop("agent_id", "")))
        agent_name = str(meta.pop("agent_name"))
        kind = meta.pop("kind") if "kind" in meta else None
        if not content:
            return None
        if isinstance(content, str):
            str_parts: List[Union[ContentPart, ReasoningPart, ToolCallPart]] = []
            if kind and kind == "reasoning":
                str_parts.append(ReasoningPart(type="reasoning", reasoning=content))
            else:
                str_parts.append(ContentPart(type="content", content=content))
            finalized_event = EmittedEvent(
                correlation_id=correlation_id,
                id=event_id,
                source="ai_agent",
                type="message",
                data=MessageEventData(
                    type="message",
                    parts=str_parts,
                    participant=Participant(id=agent_id, name=agent_name),
                ),
                metadata=meta,
            )
        elif isinstance(content, list):
            if all(isinstance(item, str) for item in content):
                content = "".join(map(str, content))  # Join strings into a single string
                # Otherwise, keep content as is (list of objects)
            list_parts: List[Union[ContentPart, ReasoningPart, ToolCallPart]] = []
            if kind and kind == "reasoning":
                list_parts.append(ReasoningPart(type="reasoning", reasoning=content))
            else:
                list_parts.append(ContentPart(type="content", content=content))
            finalized_event = EmittedEvent(
                correlation_id=correlation_id,
                id=event_id,
                source="ai_agent",
                type="message",
                data=MessageEventData(
                    type="message",
                    parts=list_parts,
                    participant=Participant(id=agent_id, name=agent_name),
                ),
                metadata=meta,
            )
        elif isinstance(content, dict):
            if "tool_calls" in content:
                # TODO this could be more type safe
                tool_call_parts: list[dict[str, JSONSerializable]] = cast(
                    list[dict[str, JSONSerializable]], content["tool_calls"]
                )
                tcpl: List[Union[ContentPart, ReasoningPart, ToolCallPart]] = []
                for tool_call in tool_call_parts:
                    args = tool_call["args"]
                    if isinstance(args, list):
                        args_as_list: list[str] = cast(list[str], args)
                        json_string = "".join(args_as_list)
                        final_args = json.loads(json_string)
                    elif isinstance(args, dict):
                        final_args = args
                    else:
                        raise ValueError("args is not a list or dict")
                    tool_part = ToolCallPart(
                        type=cast(ToolCallPartType, tool_call["type"]),
                        tool_call_id=cast(str, tool_call["tool_call_id"]),
                        tool_name=cast(str, tool_call["tool_name"]),
                        args=final_args,
                    )
                    tcpl.append(tool_part)

                # if tool_call_parts[0]["type"] == TOOL_CALL_PART_TYPE:
                finalized_event = EmittedEvent(
                    correlation_id=correlation_id,
                    id=event_id,
                    source="ai_agent",
                    type="message",
                    data=MessageEventData(
                        type="message",
                        parts=tcpl,
                        participant=Participant(id=agent_id, name=agent_name),
                    ),
                )
            elif "tool_call_results" in content:
                # elif tool_calls[0]["type"] == TOOL_CALL_RESULT_TYPE:
                # TODO this could be more type safe
                tool_calls: list[dict[str, JSONSerializable]] = cast(
                    list[dict[str, JSONSerializable]], content["tool_call_results"]
                )
                tcl: list[ToolCall] = []
                for tool_call in tool_calls:
                    tc = ToolCall(
                        tool_call_id=cast(str, tool_call["tool_call_id"]),
                        tool_name=cast(str, tool_call["tool_name"]),
                        args=cast(dict[str, JSONSerializable], tool_call["args"]),
                        result=ToolResult(
                            data=tool_call["data"]["result"]
                            if isinstance(tool_call["data"], dict)
                            else None,
                            metadata={},
                            control={"mode": "auto"},
                        ),
                    )
                    tcl.append(tc)
                finalized_event = EmittedEvent(
                    correlation_id=correlation_id,
                    id=event_id,
                    source="ai_agent",
                    type="tool",
                    data=ToolEventData(type="tool_call_result", tool_calls=tcl),
                )
                # else:
                #     raise ValueError("Finalized tool event is unrecognized")
            else:
                parts: List[Union[ContentPart, ReasoningPart, ToolCallPart]] = []
                if kind and kind == "reasoning":
                    parts.append(ReasoningPart(type="reasoning", reasoning=content))
                else:
                    parts.append(ContentPart(type="content", content=content))
                finalized_event = EmittedEvent(
                    correlation_id=correlation_id,
                    id=event_id,
                    source="ai_agent",
                    type="message",
                    data=MessageEventData(
                        type="message",
                        parts=parts,
                        participant=Participant(id=agent_id, name=agent_name),
                    ),
                    metadata=meta,
                )
        else:
            raise ValueError("Finalized event is unrecognized")
        self.finalized_events[event_id] = finalized_event
        return finalized_event
