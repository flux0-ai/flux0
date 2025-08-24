import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, Required, Sequence, Tuple, TypedDict, cast

from flux0_core.agent_runners.api import AgentRunner, Deps, agent_runner
from flux0_core.agent_runners.context import Context
from flux0_core.recordings import (
    RecordedChunkPayload,
    RecordedEmittedPayload,
    RecordedEvent,
    RecordingId,
)
from flux0_core.sessions import EventId, Session, SessionUpdateParams, StatusEventData
from flux0_stream.types import ChunkEvent


class ReplayMeta(TypedDict, total=False):
    recording_id: Required[RecordingId]
    pacing: Required[float]
    last_streamed_offset: Required[int]


# ---- helpers ---------------------------------------------------------------


def get_replay_meta(session: Session) -> Optional[ReplayMeta]:
    """
    Extract/normalize replay meta from session.metadata.
    Returns None if this is not a replay session.
    """
    md = getattr(session, "metadata", None) or {}
    rm = cast(Optional[ReplayMeta], md.get("replay"))
    if not rm or "recording_id" not in rm:
        return None

    # Defaults
    if "pacing" not in rm or rm["pacing"] is None:
        rm["pacing"] = 1.0
    if "last_streamed_offset" not in rm:
        rm["last_streamed_offset"] = 0

    return rm


def _utc_ts(dt: datetime) -> float:
    """Convert tz-aware datetime to UNIX seconds (safe for ChunkEvent.timestamp)."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        # Should not happen; store should have saved tz-aware UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


async def _paced_iter(
    frames: Sequence[RecordedEvent],
    pace: float,
) -> AsyncIterator[RecordedEvent]:
    """
    Yield frames with pacing.
    pace: 0.0 => instant, 1.0 => record-time, >1.0 slower, <1.0 faster.
    Accepts any Sequence[RecordedEvent] to play nicely with store return types.
    """
    if not frames:
        return
    # First frame emits immediately (no delay)
    prev = frames[0].created_at
    yield frames[0]
    for f in frames[1:]:
        if pace > 0.0:
            delta = max(0.0, (f.created_at - prev).total_seconds())
            await asyncio.sleep(delta * pace)
        prev = f.created_at
        yield f


# ---- runner ----------------------------------------------------------------


@agent_runner("replay")
class ReplayAgentRunner(AgentRunner):
    """
    Replays recorded frames for a session turn:
      • Finds the next user-anchored turn after session.metadata.replay.last_streamed_offset
      • Streams [start, end) as live events via the EventEmitter
      • Paces by recorded created_at deltas (with clamping, factor = pacing)
      • Updates last_streamed_offset when done
    """

    async def run(self, context: Context, deps: Deps) -> bool:
        # Load session to get replay metadata
        session = await deps.read_session(context.session_id)
        if not session:
            deps.logger.error("ReplayAgentRunner: session not found")
            return False

        rmeta = get_replay_meta(session)
        if not rmeta:
            deps.logger.error("ReplayAgentRunner: missing replay metadata")
            return False

        # ---- required replay parameters ----
        recording_id = rmeta["recording_id"]
        if not recording_id:
            deps.logger.error("ReplayAgentRunner: missing recording_id in session.metadata.replay")
            # Signal completion to UI so it doesn't hang
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
            return False

        pacing = rmeta["pacing"]
        after = rmeta["last_streamed_offset"]

        # ---- compute the next turn range ----
        rng: Optional[
            Tuple[int, Optional[int]]
        ] = await deps._recording_store.read_next_turn_range_after_offset(
            recording_id=recording_id,
            after_offset=after,
        )
        if not rng:
            # Nothing left to replay — emit a soft completion and exit
            deps.logger.info("ReplayAgentRunner: no more turns to replay")
            await deps.event_emitter.enqueue_status_event(
                correlation_id=deps.correlator.correlation_id,
                data=StatusEventData(type="status", status="completed"),
            )
            return True

        start, end = rng

        # ---- read frames for that range ----
        frames: Sequence[RecordedEvent] = await deps._recording_store.read_frames_range(
            recording_id=recording_id,
            start_offset_inclusive=start,
            end_offset_exclusive=end,
        )

        if not frames:
            # Shouldn't happen, but avoid updating cursor incorrectly
            deps.logger.warning(
                "ReplayAgentRunner: empty frame range for %s [%s,%s)", recording_id, start, end
            )
            return True

        # ---- stream frames with pacing ----
        current_correlation = (
            deps.correlator.correlation_id
        )  # rewrite to this session's correlation
        last_offset_streamed = after

        async for f in _paced_iter(frames, pacing):
            last_offset_streamed = f.offset

            if f.kind == "chunk":
                p = cast(RecordedChunkPayload, f.payload)
                meta = p.get("metadata") or {}
                # Rebuild a ChunkEvent using current correlation_id, keep original event_id/seq/patches
                ce = ChunkEvent(
                    correlation_id=current_correlation,
                    event_id=p["event_id"],
                    seq=p["seq"],
                    patches=p["patches"],
                    metadata=meta,
                    timestamp=_utc_ts(f.created_at),
                )
                await deps.event_emitter.enqueue_event_chunk(ce)

            elif f.kind == "emitted":
                ep = cast(RecordedEmittedPayload, f.payload)
                etype = ep["type"]

                if etype == "status":
                    data = cast(StatusEventData, ep["data"])  # StatusEventData shape
                    raw_id = cast(str, ep.get("id", ""))
                    # Use recorded id if present; otherwise synthesize one to help client SSE idempotency
                    eid = EventId(raw_id) if raw_id else EventId(uuid.uuid4().hex)
                    await deps.event_emitter.enqueue_status_event(
                        correlation_id=current_correlation,
                        data=data,
                        event_id=eid,
                    )
                else:
                    # For v1, emitted tool/custom (if any) are not required to be re-enqueued.
                    # If you later expose enqueue_tool/custom, map them here.
                    deps.logger.debug("ReplayAgentRunner: skipping emitted type=%s", etype)

            else:
                # header never appears here; ignore unknown kind safely
                deps.logger.debug(
                    "ReplayAgentRunner: skipping kind=%s at offset=%s", f.kind, f.offset
                )

        # ---- advance the cursor on the session ----
        rmeta["last_streamed_offset"] = last_offset_streamed
        md = getattr(session, "metadata", {}) or {}
        md["replay"] = rmeta
        await deps._session_store.update_session(
            session.id,
            SessionUpdateParams(metadata=md),
        )

        return True
