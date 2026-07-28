from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.context import RequestContext, get_request_context
from observelens_knowledge_base.common.dependencies import get_session
from observelens_knowledge_base.retrieval.repository import RetrievalRepository
from observelens_knowledge_base.retrieval.schemas import (
    InternalContextRetrieveRequest,
    InternalContextRetrieveResponse,
    RetrievalFeedbackRequest,
    RetrievalFeedbackResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from observelens_knowledge_base.retrieval.service import RetrievalService

router = APIRouter(tags=["Retrieval"])


def get_retrieval_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RetrievalService:
    return RetrievalService(RetrievalRepository(session))


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
async def search_knowledge(
    request: RetrievalSearchRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalSearchResponse:
    return await service.search(ctx, request)


@router.post("/retrieval/feedback", response_model=RetrievalFeedbackResponse, status_code=201)
async def submit_retrieval_feedback(
    request: RetrievalFeedbackRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalFeedbackResponse:
    return await service.submit_feedback(ctx, request)


@router.post("/internal/v1/context/retrieve", response_model=InternalContextRetrieveResponse)
async def retrieve_internal_context(
    request: InternalContextRetrieveRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> InternalContextRetrieveResponse:
    return await service.retrieve_context(ctx, request)
