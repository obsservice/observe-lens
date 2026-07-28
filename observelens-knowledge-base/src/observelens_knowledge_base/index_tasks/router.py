from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.context import RequestContext, get_request_context
from observelens_knowledge_base.common.dependencies import get_session
from observelens_knowledge_base.documents.schemas import IndexTaskResponse
from observelens_knowledge_base.index_tasks.repository import IndexTaskRepository
from observelens_knowledge_base.index_tasks.service import IndexTaskService

router = APIRouter(prefix="/index-tasks", tags=["IndexTask"])


def get_index_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IndexTaskService:
    return IndexTaskService(IndexTaskRepository(session))


@router.get("/{task_id}", response_model=IndexTaskResponse)
async def get_index_task(
    task_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[IndexTaskService, Depends(get_index_task_service)],
) -> IndexTaskResponse:
    return await service.get(ctx, task_id)


@router.post("/{task_id}/retry", response_model=IndexTaskResponse, status_code=202)
async def retry_index_task(
    task_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[IndexTaskService, Depends(get_index_task_service)],
) -> IndexTaskResponse:
    return await service.retry(ctx, task_id)
