from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.clients.agent import AgentClient
from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.config.settings import get_settings
from observelens_service.database.session import session_scope
from observelens_service.modules.conversations.schemas import (
    ConversationCreateRequest,
    ConversationPage,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageCreateRequest,
)
from observelens_service.modules.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversation"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[ConversationService]:
    settings = get_settings()
    async with session_scope(factory) as session:
        yield ConversationService(
            session, AgentClient(str(settings.agent_base_url), settings.agent_timeout_seconds)
        )


ServiceDependency = Annotated[ConversationService, Depends(get_service)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]


@router.get("", response_model=ConversationPage)
async def list_conversations(
    context: ContextDependency,
    service: ServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ConversationPage:
    return await service.list(context, page, page_size)


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: ConversationCreateRequest, context: ContextDependency, service: ServiceDependency
) -> ConversationResponse:
    return await service.create(context, request)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int, context: ContextDependency, service: ServiceDependency
) -> ConversationResponse:
    return await service.get(context, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> ConversationResponse:
    return await service.update(context, conversation_id, request)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int, context: ContextDependency, service: ServiceDependency
) -> Response:
    await service.delete(context, conversation_id)
    return Response(status_code=204)


@router.post("/{conversation_id}/messages", response_class=StreamingResponse)
async def create_message(
    conversation_id: int,
    request: MessageCreateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> StreamingResponse:
    _, run_id = await service.create_message(context, conversation_id, request.content)
    return StreamingResponse(
        service.stream_run(conversation_id, run_id, request.content),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
