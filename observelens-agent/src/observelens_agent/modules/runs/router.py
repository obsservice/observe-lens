import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.modules.runs.schemas import RunStreamRequest

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.post(":stream")
async def stream_run(request: RunStreamRequest, http_request: Request) -> StreamingResponse:
    graph: CompiledStateGraph[Any] = http_request.app.state.agent_graph

    async def event_stream() -> AsyncIterator[str]:
        yield json.dumps({"run_id": request.run_id, "event": "started"}) + "\n"

        result: dict[str, Any] = await graph.ainvoke({"msg": request.content})

        yield (
            json.dumps(
                {
                    "run_id": request.run_id,
                    "event": "completed",
                    "output": result["msg"],
                }
            )
            + "\n"
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
