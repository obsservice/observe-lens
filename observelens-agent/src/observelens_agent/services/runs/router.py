import json
from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.services.runs.schemas import RunStreamRequest

router = APIRouter(prefix="/runs", tags=["Runs"])
logger = structlog.get_logger(__name__)


def extract_sse_event(stream_chunk: Mapping[str, object]) -> str | None:
    """Return the SSE event from a custom LangGraph stream chunk."""
    sse_event = stream_chunk.get("sse")
    return sse_event if isinstance(sse_event, str) else None


def _unpack_stream_event(stream_event: object) -> tuple[str, object] | None:
    if not isinstance(stream_event, tuple):
        return None
    if len(stream_event) == 2:
        mode, data = stream_event
    elif len(stream_event) == 3:
        _, mode, data = stream_event
    else:
        return None
    return (mode, data) if isinstance(mode, str) else None


def _build_run_event(
    event_type: str,
    conversation_id: str,
    run_id: str,
    sequence: int,
    data: dict[str, object],
) -> str:
    payload = {
        "conversation_id": conversation_id,
        "run_id": run_id,
        "sequence": sequence,
        "id": f"run-{run_id}-{sequence}",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return (
        f"event: {event_type}\nid: {payload['id']}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    )


@router.post(":stream")
async def stream_run(request: RunStreamRequest, http_request: Request) -> StreamingResponse:
    graph: CompiledStateGraph[Any] = http_request.app.state.agent_graph
    input_state: dict[str, Any] = {
        "conversation_id": request.conversation_id,
        "run_id": request.run_id,
        "msg": request.content,
    }

    async def event_stream() -> AsyncIterator[str]:
        started_at = perf_counter()
        custom_event_count = 0
        run_failure_message: str | None = None

        yield _build_run_event(
            "run.started",
            request.conversation_id,
            request.run_id,
            sequence=1,
            data={"agent": "observelens-agent"},
        )

        try:
            async for stream_event in graph.astream(
                input_state,
                stream_mode=["custom", "values"],
                subgraphs=True,
            ):
                unpacked_event = _unpack_stream_event(stream_event)
                if unpacked_event is None:
                    continue
                mode, data = unpacked_event
                if mode == "custom" and isinstance(data, dict):
                    sse = extract_sse_event(data)
                    if sse:
                        custom_event_count += 1
                        yield sse
                elif mode == "values" and isinstance(data, dict):
                    failure_message = data.get("run_failure_message")
                    if isinstance(failure_message, str):
                        run_failure_message = failure_message
        except Exception:
            logger.exception("run_stream_failed", run_id=request.run_id)
            run_failure_message = "Agent run failed unexpectedly."

        sequence = custom_event_count + 2
        if run_failure_message is not None:
            yield _build_run_event(
                "run.failed",
                request.conversation_id,
                request.run_id,
                sequence=sequence,
                data={"message": run_failure_message},
            )
            return

        yield _build_run_event(
            "run.completed",
            request.conversation_id,
            request.run_id,
            sequence=sequence,
            data={"duration_ms": round((perf_counter() - started_at) * 1000)},
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
