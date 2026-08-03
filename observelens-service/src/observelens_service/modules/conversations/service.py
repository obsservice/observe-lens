from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.clients.agent import AgentClient
from observelens_service.common.context import RequestContext
from observelens_service.common.exceptions import ResourceNotFoundError
from observelens_service.modules.conversations.models import (
    ConversationModel,
    MessageModel,
    RunModel,
)
from observelens_service.modules.conversations.repository import ConversationRepository
from observelens_service.modules.conversations.schemas import (
    ConversationCreateRequest,
    ConversationPage,
    ConversationResponse,
    ConversationUpdateRequest,
    MessagePage,
    MessageResponse,
)

logger = structlog.get_logger(__name__)


def new_id() -> int:
    """Generate a sortable BIGINT identifier before a shared ID service is introduced."""
    return time.time_ns() // 1_000


class ConversationService:
    def __init__(self, session: AsyncSession, agent_client: AgentClient) -> None:
        self._session = session
        self._repository = ConversationRepository(session)
        self._agent_client = agent_client

    async def list(self, context: RequestContext, page: int, page_size: int) -> ConversationPage:
        rows, total = await self._repository.list(context.tenant_id, page, page_size)
        return ConversationPage(
            items=[ConversationResponse.model_validate(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create(
        self, context: RequestContext, request: ConversationCreateRequest
    ) -> ConversationResponse:
        conversation = ConversationModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            owner_id=context.user_id,
            title=request.title or "New investigation",
            status="ACTIVE",
            create_time=datetime.now(UTC),
            update_time=datetime.now(UTC),
        )
        self._repository.add(conversation)
        await self._session.flush()
        return ConversationResponse.model_validate(conversation)

    async def get(self, context: RequestContext, conversation_id: int) -> ConversationResponse:
        conversation = await self._require(context, conversation_id)
        return ConversationResponse.model_validate(conversation)

    async def list_messages(
        self, context: RequestContext, conversation_id: int, page: int, page_size: int
    ) -> MessagePage:
        await self._require(context, conversation_id)
        rows, total = await self._repository.list_messages(
            context.tenant_id, conversation_id, page, page_size
        )
        return MessagePage(
            items=[MessageResponse.model_validate(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(
        self, context: RequestContext, conversation_id: int, request: ConversationUpdateRequest
    ) -> ConversationResponse:
        conversation = await self._require(context, conversation_id)
        if request.title is not None:
            conversation.title = request.title
        if request.status is not None:
            conversation.status = request.status
        await self._session.flush()
        return ConversationResponse.model_validate(conversation)

    async def delete(self, context: RequestContext, conversation_id: int) -> None:
        conversation = await self._require(context, conversation_id)
        from datetime import UTC, datetime

        conversation.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def create_message(
        self, context: RequestContext, conversation_id: int, content: str
    ) -> tuple[MessageResponse, int]:
        await self._require(context, conversation_id)
        message = MessageModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            sequence_id=await self._repository.next_message_sequence(
                context.tenant_id, conversation_id
            ),
            sender_role="USER",
            content=content,
            status="COMPLETED",
        )
        run = RunModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            input_message_id=message.id,
            status="PENDING",
        )
        message.run_id = run.id
        self._repository.add(message)
        self._repository.add(run)
        await self._session.flush()
        return MessageResponse.model_validate(message), run.id

    async def stream_run(
        self,
        conversation_id: int,
        run_id: int,
        content: str,
        tenant_id: int | None = None,
    ) -> AsyncIterator[str]:
        assistant_content = ""
        investigation_events: list[dict[str, object]] = []
        try:
            async for event in self._agent_client.stream_run(conversation_id, run_id, content):
                yield event
                payload = self._parse_event(event)
                if payload is not None:
                    investigation_events.append(payload)
                output = self._extract_output(event, payload)
                if output is not None:
                    event_type, event_content = output
                    if event_type == "output.completed":
                        assistant_content = event_content
                    elif event_type == "output.progress":
                        assistant_content += event_content
        except httpx.TimeoutException:
            logger.warning("agent_run_timed_out", conversation_id=conversation_id, run_id=run_id)
            yield self._run_failed_event(
                conversation_id, run_id, "AGENT_TIMEOUT", "Agent Runtime request timed out"
            )
        except httpx.RequestError:
            logger.warning(
                "agent_runtime_unavailable", conversation_id=conversation_id, run_id=run_id
            )
            yield self._run_failed_event(
                conversation_id,
                run_id,
                "AGENT_UNAVAILABLE",
                "Agent Runtime is unavailable. Verify its URL and status.",
            )
        except httpx.HTTPStatusError:
            logger.warning(
                "agent_runtime_request_failed", conversation_id=conversation_id, run_id=run_id
            )
            yield self._run_failed_event(
                conversation_id,
                run_id,
                "AGENT_REQUEST_FAILED",
                "Agent Runtime rejected the investigation request.",
            )
        finally:
            if tenant_id is not None and assistant_content.strip():
                await self._persist_assistant_message(
                    tenant_id,
                    conversation_id,
                    run_id,
                    assistant_content,
                    investigation_events,
                )

    @staticmethod
    def _parse_event(event: str) -> dict[str, object] | None:
        for line in event.splitlines():
            if line.startswith("data:"):
                try:
                    payload = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    return None
                return payload if isinstance(payload, dict) else None
        return None

    @staticmethod
    def _extract_output(
        event: str, payload: dict[str, object] | None = None
    ) -> tuple[str, str] | None:
        output_payload = payload or ConversationService._parse_event(event)
        if output_payload is None:
            return None
        event_type = output_payload.get("type")
        data = output_payload.get("data")
        if event_type not in {"output.progress", "output.completed"} or not isinstance(data, dict):
            return None
        value = data.get("content")
        return str(event_type), value if isinstance(value, str) else ""

    async def _persist_assistant_message(
        self,
        tenant_id: int,
        conversation_id: int,
        run_id: int,
        content: str,
        investigation_events: list[dict[str, object]],
    ) -> None:
        message = MessageModel(
            id=new_id(),
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            sequence_id=await self._repository.next_message_sequence(
                tenant_id, conversation_id
            ),
            run_id=run_id,
            sender_role="ASSISTANT",
            content=content,
            message_metadata={"events": investigation_events},
            status="COMPLETED",
        )
        self._repository.add(message)
        await self._session.flush()

    @staticmethod
    def _run_failed_event(conversation_id: int, run_id: int, code: str, message: str) -> str:
        payload = {
            "id": f"service-{run_id}-{time.time_ns()}",
            "type": "run.failed",
            "timestamp": datetime.now(UTC).isoformat(),
            "conversation_id": str(conversation_id),
            "run_id": str(run_id),
            "sequence": 1,
            "data": {"code": code, "message": message},
        }
        return f"event: run.failed\ndata: {json.dumps(payload)}\n\n"

    async def _require(self, context: RequestContext, conversation_id: int) -> ConversationModel:
        conversation = await self._repository.get(context.tenant_id, conversation_id)
        if conversation is None:
            raise ResourceNotFoundError("Conversation")
        return conversation
