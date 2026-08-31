from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.clients.agent import AgentClient
from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.config.settings import get_settings
from observelens_service.database.session import session_scope
from observelens_service.modules.inspections.execution import execute_inspection_agent
from observelens_service.modules.inspections.schemas import (
    InspectionCreateRequest,
    InspectionExecutionResponse,
    InspectionPage,
    InspectionResponse,
    InspectionUpdateRequest,
)
from observelens_service.modules.inspections.service import InspectionService

router = APIRouter(prefix="/inspections", tags=["Inspection"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[InspectionService]:
    async with session_scope(factory) as session:
        yield InspectionService(session)


ServiceDependency = Annotated[InspectionService, Depends(get_service)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]
SessionFactoryDependency = Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)]


def get_agent_client() -> AgentClient:
    settings = get_settings()
    return AgentClient(str(settings.agent_base_url), settings.agent_timeout_seconds)


AgentDependency = Annotated[AgentClient, Depends(get_agent_client)]


@router.get("", response_model=InspectionPage)
async def list_inspections(
    context: ContextDependency,
    service: ServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> InspectionPage:
    return await service.list(context, page, page_size)


@router.post("", response_model=InspectionResponse, status_code=201)
async def create_inspection(
    request: InspectionCreateRequest, context: ContextDependency, service: ServiceDependency
) -> InspectionResponse:
    return await service.create(context, request)


@router.get("/statuses")
async def list_statuses(context: ContextDependency) -> list[dict[str, str]]:
    return [
        {"value": value, "label": value.title()}
        for value in ("ENABLED", "DISABLED", "RUNNING", "SUCCESS", "FAILED")
    ]


@router.get("/schedules")
async def list_schedules(context: ContextDependency) -> list[dict[str, str]]:
    return [
        {"value": "Every Hour", "label": "Every Hour"},
        {"value": "Every Day", "label": "Every Day"},
        {"value": "CRON: 0 * * * *", "label": "Custom cron"},
    ]


@router.get("/{inspection_id:int}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: int, context: ContextDependency, service: ServiceDependency
) -> InspectionResponse:
    return await service.get(context, inspection_id)


@router.patch("/{inspection_id:int}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: int,
    request: InspectionUpdateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> InspectionResponse:
    return await service.update(context, inspection_id, request)


@router.delete("/{inspection_id:int}", status_code=204)
async def delete_inspection(
    inspection_id: int, context: ContextDependency, service: ServiceDependency
) -> Response:
    await service.delete(context, inspection_id)
    return Response(status_code=204)


@router.post(
    "/{inspection_id:int}/execute", response_model=InspectionExecutionResponse, status_code=202
)
async def execute_inspection(
    inspection_id: int,
    context: ContextDependency,
    service: ServiceDependency,
    background_tasks: BackgroundTasks,
    agent_client: AgentDependency,
    factory: SessionFactoryDependency,
) -> InspectionExecutionResponse:
    execution = await service.execute(context, inspection_id)
    background_tasks.add_task(
        execute_inspection_agent,
        agent_client,
        factory,
        context.tenant_id,
        execution.task_id,
        execution.response.run_id,
        execution.content,
    )
    return execution.response


@router.post("/{inspection_id:int}/enable", response_model=InspectionResponse)
async def enable_inspection(
    inspection_id: int, context: ContextDependency, service: ServiceDependency
) -> InspectionResponse:
    return await service.set_enabled(context, inspection_id, True)


@router.post("/{inspection_id:int}/disable", response_model=InspectionResponse)
async def disable_inspection(
    inspection_id: int, context: ContextDependency, service: ServiceDependency
) -> InspectionResponse:
    return await service.set_enabled(context, inspection_id, False)
