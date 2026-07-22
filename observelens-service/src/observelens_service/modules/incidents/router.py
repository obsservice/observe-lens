from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.database.session import session_scope
from observelens_service.modules.incidents.schemas import (
    IncidentCreateRequest,
    IncidentIntegrationResponse,
    IncidentPage,
    IncidentResponse,
    IncidentUpdateRequest,
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    OpenConversationResponse,
)
from observelens_service.modules.incidents.service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incident"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[IncidentService]:
    async with session_scope(factory) as session:
        yield IncidentService(session)


ServiceDependency = Annotated[IncidentService, Depends(get_service)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]


@router.get("", response_model=IncidentPage)
async def list_incidents(
    context: ContextDependency,
    service: ServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    status: str | None = None,
) -> IncidentPage:
    return await service.list(context, page, page_size, severity, status)


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    request: IncidentCreateRequest, context: ContextDependency, service: ServiceDependency
) -> IncidentResponse:
    return await service.create(context, request)


@router.get("/severities")
async def list_severities() -> list[dict[str, str]]:
    return [
        {"value": value, "label": value.title()} for value in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    ]


@router.get("/statuses")
async def list_statuses() -> list[dict[str, str]]:
    return [
        {"value": value, "label": value.title()}
        for value in ("OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED", "CLOSED", "ARCHIVED")
    ]


@router.get("/sources")
async def list_sources() -> list[dict[str, str]]:
    return [
        {"value": value, "label": value.title()}
        for value in ("ALERTMANAGER", "GRAFANA", "MANUAL", "WEBHOOK")
    ]


@router.get("/{incident_id:int}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int, context: ContextDependency, service: ServiceDependency
) -> IncidentResponse:
    return await service.get(context, incident_id)


@router.patch("/{incident_id:int}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    request: IncidentUpdateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> IncidentResponse:
    return await service.update(context, incident_id, request)


@router.delete("/{incident_id:int}", status_code=204)
async def delete_incident(
    incident_id: int, context: ContextDependency, service: ServiceDependency
) -> Response:
    await service.delete(context, incident_id)
    return Response(status_code=204)


@router.post("/{incident_id:int}/archive", response_model=IncidentResponse)
async def archive_incident(
    incident_id: int, context: ContextDependency, service: ServiceDependency
) -> IncidentResponse:
    return await service.archive(context, incident_id)


@router.post(
    "/{incident_id:int}/open-conversation",
    response_model=OpenConversationResponse,
    status_code=201,
)
async def open_incident_conversation(
    incident_id: int, context: ContextDependency, service: ServiceDependency
) -> OpenConversationResponse:
    return await service.open_conversation(context, incident_id)


@router.get("/integrations", response_model=list[IncidentIntegrationResponse])
async def list_integrations(
    context: ContextDependency, service: ServiceDependency
) -> list[IncidentIntegrationResponse]:
    return await service.list_integrations(context)


@router.post("/integrations", response_model=IncidentIntegrationResponse, status_code=201)
async def create_integration(
    request: IntegrationCreateRequest, context: ContextDependency, service: ServiceDependency
) -> IncidentIntegrationResponse:
    return await service.create_integration(context, request)


@router.get("/integrations/{integration_id}", response_model=IncidentIntegrationResponse)
async def get_integration(
    integration_id: int, context: ContextDependency, service: ServiceDependency
) -> IncidentIntegrationResponse:
    return await service.get_integration(context, integration_id)


@router.patch("/integrations/{integration_id}", response_model=IncidentIntegrationResponse)
async def update_integration(
    integration_id: int,
    request: IntegrationUpdateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> IncidentIntegrationResponse:
    return await service.update_integration(context, integration_id, request)


@router.delete("/integrations/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: int, context: ContextDependency, service: ServiceDependency
) -> Response:
    await service.delete_integration(context, integration_id)
    return Response(status_code=204)
