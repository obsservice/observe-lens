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


class AssistantAgentClient:
    async def stream_run(self, conversation_id: int, run_id: int, content: str):  # type: ignore[no-untyped-def]
        yield (
            "event: output.progress\ndata: "
            '{"type":"output.progress","data":{"content":"partial"}}\n\n'
        )
        yield (
            "event: output.completed\ndata: "
            '{"type":"output.completed","data":{"content":"final answer"}}\n\n'
        )


def test_list_common_commands_returns_chat_shortcuts() -> None:
    commands = ConversationService.list_common_commands()

    assert [command.name for command in commands] == [
        "/get_info",
        "/get_metric",
        "/analysis_incident",
    ]
    assert all(command.description and command.prompt for command in commands)


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


@pytest.mark.asyncio
async def test_stream_run_persists_failed_assistant_response() -> None:
    service = ConversationService(FakeSession(), UnavailableAgentClient())  # type: ignore[arg-type]
    captured: list[object] = []
    service._repository.add = captured.append  # type: ignore[method-assign]

    async def next_sequence(*args: object) -> int:
        return 2

    service._repository.next_message_sequence = next_sequence  # type: ignore[method-assign]

    events = [event async for event in service.stream_run(7, 11, "Investigate Kafka", tenant_id=7)]

    assert len(events) == 1
    assert len(captured) == 1
    message = captured[0]
    assert message.sender_role == "ASSISTANT"  # type: ignore[union-attr]
    assert message.status == "FAILED"  # type: ignore[union-attr]
    assert message.content == "Agent Runtime is unavailable. Verify its URL and status."  # type: ignore[union-attr]
    assert message.sequence_id == 2  # type: ignore[union-attr]
    assert message.message_metadata["events"][0]["type"] == "run.failed"  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_stream_run_persists_assistant_response() -> None:
    service = ConversationService(FakeSession(), AssistantAgentClient())  # type: ignore[arg-type]
    captured: list[object] = []
    service._repository.add = captured.append  # type: ignore[method-assign]

    async def next_sequence(*args: object) -> int:
        return 2

    service._repository.next_message_sequence = next_sequence  # type: ignore[method-assign]

    events = [event async for event in service.stream_run(7, 11, "Investigate Kafka", tenant_id=7)]

    assert len(events) == 2
    assert len(captured) == 1
    message = captured[0]
    assert message.sender_role == "ASSISTANT"  # type: ignore[union-attr]
    assert message.content == "final answer"  # type: ignore[union-attr]
    assert message.sequence_id == 2  # type: ignore[union-attr]
    assert len(message.message_metadata["events"]) == 2  # type: ignore[union-attr]
