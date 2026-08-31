import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.mock_node import extract_sse
from observelens_agent.modules.runs.schemas import RunStreamRequest

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.post(":stream")
async def stream_run(request: RunStreamRequest, http_request: Request) -> StreamingResponse:
    graph: CompiledStateGraph[Any] = http_request.app.state.agent_graph
    input_state: dict[str, Any] = {
        "msg": request.content,
        "conversation_id": request.conversation_id,
        "run_id": request.run_id,
    }

    async def event_stream() -> AsyncIterator[str]:
        intent: str = ""
        agent_output: str | None = None

        async for mode, data in graph.astream(
            input_state, stream_mode=["custom", "values"]
        ):
            if mode == "custom" and isinstance(data, dict):
                sse = extract_sse(data)
                if sse:
                    yield sse
            elif mode == "values" and isinstance(data, dict):
                if "intent" in data:
                    intent = data["intent"]
                if intent != "mock" and "msg" in data:
                    agent_output = data["msg"]

        if agent_output is not None:
            yield json.dumps(
                {
                    "run_id": request.run_id,
                    "conversation_id": request.conversation_id,
                    "event": "completed",
                    "output": agent_output,
                },
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
