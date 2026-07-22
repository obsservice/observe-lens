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
        self, conversation_id: int, run_id: int, content: str
    ) -> AsyncIterator[str]:
        try:
            async for event in self._agent_client.stream_run(conversation_id, run_id, content):
                yield event
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
