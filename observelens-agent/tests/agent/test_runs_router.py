import json
from types import SimpleNamespace
from typing import Any

import pytest

from observelens_agent.services.runs.router import (
    _build_run_event,
    extract_sse_event,
    stream_run,
)
from observelens_agent.services.runs.schemas import RunStreamRequest


class FakeGraph:
    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events
        self.input_state: dict[str, Any] | None = None
        self.stream_mode: list[str] | None = None
        self.subgraphs: bool | None = None

    async def astream(
        self, input_state: dict[str, Any], stream_mode: list[str], subgraphs: bool
    ) -> Any:
        self.input_state = input_state
        self.stream_mode = stream_mode
        self.subgraphs = subgraphs
        for event in self._events:
            yield event


async def _stream_events(graph: FakeGraph) -> list[str]:
    request = RunStreamRequest(
        conversation_id="conversation-1",
        run_id="run-1",
        content="inspect the cluster",
    )
    http_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(agent_graph=graph)))
    response = await stream_run(request, http_request)
    return [event async for event in response.body_iterator]


def test_extract_sse_event_returns_only_string_events() -> None:
    assert extract_sse_event({"sse": "event: run.started\n\n"}) == "event: run.started\n\n"
    assert extract_sse_event({"sse": {"type": "run.started"}}) is None
    assert extract_sse_event({}) is None


def test_build_run_event_uses_aesp_envelope() -> None:
    event = _build_run_event(
        "run.completed",
        "conversation-1",
        "run-1",
        sequence=4,
        data={"duration_ms": 42},
    )

    assert event.startswith("event: run.completed\n")
    payload = json.loads(event.split("data: ", maxsplit=1)[1])
    assert payload["type"] == "run.completed"
    assert payload["sequence"] == 4
    assert payload["data"]["duration_ms"] == 42


@pytest.mark.asyncio
async def test_stream_run_forwards_graph_events_between_run_events() -> None:
    graph = FakeGraph(
        [
            (("rca:task-1",), "custom", {"sse": "event: analysis.generated\ndata: {}\n\n"}),
            ("values", {"run_failure_message": None}),
        ]
    )

    events = await _stream_events(graph)

    assert events[0].startswith("event: run.started\n")
    assert events[1] == "event: analysis.generated\ndata: {}\n\n"
    assert events[2].startswith("event: run.completed\n")
    assert graph.stream_mode == ["custom", "values"]
    assert graph.subgraphs is True
    assert graph.input_state == {
        "conversation_id": "conversation-1",
        "run_id": "run-1",
        "msg": "inspect the cluster",
    }


@pytest.mark.asyncio
async def test_stream_run_emits_run_failed_for_graph_failure_state() -> None:
    graph = FakeGraph([("values", {"run_failure_message": "Catalog unavailable"})])

    events = await _stream_events(graph)

    assert events[0].startswith("event: run.started\n")
    assert events[1].startswith("event: run.failed\n")
    assert "run.completed" not in events[1]
