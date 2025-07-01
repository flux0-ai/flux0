from flux0_core.agent_runners.api import Deps
from flux0_core.sessions import (
    StatusEventData,
)
from flux0_stream.emitter.api import EventEmitter

STATUS_EVENT_DATA_KEY = "detail"


async def send_processing_event(deps: Deps, content: str) -> None:
    await emit_processing_event(
        event_emitter=deps.event_emitter,
        correlation_id=deps.correlator.correlation_id,
        content=content,
    )


async def emit_processing_event(
    event_emitter: EventEmitter, correlation_id: str, content: str
) -> None:
    await event_emitter.enqueue_status_event(
        correlation_id=correlation_id,
        data=StatusEventData(
            type="status", status="processing", data={STATUS_EVENT_DATA_KEY: content}
        ),
    )
