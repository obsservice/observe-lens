from datetime import datetime

import httpx
import pytest

from observelens_service.common.context import RequestContext
from observelens_service.modules.conversations.models import ConversationModel
from observelens_service.modules.conversations.schemas import ConversationCreateRequest
from observelens_service.modules.conversations.service import ConversationService


class FakeSession:
    async def flush(self) -> None:
        return None


class FakeAgentClient:
    async def stream_run(self, conversation_id: int, run_id: int, content: str):  # type: ignore[no-untyped-def]
        yield "event: run.started\n\n"


class UnavailableAgentClient:
    async def stream_run(self, conversation_id: int, run_id: int, content: str):  # type: ignore[no-untyped-def]
        raise httpx.ConnectError("connection refused")
        yield ""


@pytest.mark.asyncio
async def test_create_conversation_uses_request_context(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ConversationService(FakeSession(), FakeAgentClient())  # type: ignore[arg-type]
    captured: list[ConversationModel] = []
    monkeypatch.setattr(service._repository, "add", captured.append)
    response = await service.create(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        ConversationCreateRequest(title="Kafka RCA"),
    )
    assert response.title == "Kafka RCA"
    assert captured[0].tenant_id == 7
    assert captured[0].owner_id == 11
    assert captured[0].create_time is None or isinstance(captured[0].create_time, datetime)


@pytest.mark.asyncio
async def test_stream_run_returns_aesp_failure_when_agent_is_unavailable() -> None:
    service = ConversationService(FakeSession(), UnavailableAgentClient())  # type: ignore[arg-type]
    events = [event async for event in service.stream_run(7, 11, "Investigate Kafka")]
    assert len(events) == 1
    assert events[0].startswith("event: run.failed\n")
    assert '"code": "AGENT_UNAVAILABLE"' in events[0]
