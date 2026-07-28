from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.context import RequestContext, get_request_context
from observelens_knowledge_base.common.dependencies import get_session
from observelens_knowledge_base.common.enums import KnowledgeBaseStatus
from observelens_knowledge_base.knowledge_bases.repository import KnowledgeBaseRepository
from observelens_knowledge_base.knowledge_bases.schemas import (
    CreateKnowledgeBaseRequest,
    KnowledgeBasePage,
    KnowledgeBaseResponse,
    UpdateKnowledgeBaseRequest,
)
from observelens_knowledge_base.knowledge_bases.service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["KnowledgeBase"])


def get_knowledge_base_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> KnowledgeBaseService:
    return KnowledgeBaseService(KnowledgeBaseRepository(session), request.app.state.settings)


@router.get("", response_model=KnowledgeBasePage)
async def list_knowledge_bases(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    keyword: str | None = None,
    status: KnowledgeBaseStatus | None = None,
) -> KnowledgeBasePage:
    return await service.list(ctx, page, page_size, keyword, status)


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseResponse:
    return await service.create(ctx, request)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseResponse:
    return await service.get(ctx, knowledge_base_id)


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    request: UpdateKnowledgeBaseRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseResponse:
    return await service.update(ctx, knowledge_base_id, request)


@router.delete("/{knowledge_base_id}", status_code=204)
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> Response:
    await service.delete(ctx, knowledge_base_id)
    return Response(status_code=204)
