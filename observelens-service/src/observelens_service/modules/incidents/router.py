from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.database.session import session_scope
from observelens_service.modules.incidents.schemas import (
    SUPPORTED_INCIDENT_SEVERITIES,
    SUPPORTED_INCIDENT_STATUSES,
    SUPPORTED_INTEGRATION_TYPES,
    TRANSITION_RULES,
    AlertmanagerWebhookRequest,
    IncidentIntegrationResponse,
    IncidentPage,
    IncidentResponse,
    IncidentUpdateRequest,
    IntegrationCreateRequest,
    IntegrationStatus,
    IntegrationType,
    IntegrationUpdateRequest,
    TransitionRequest,
    OpenConversationResponse,
    WebhookIncidentRequest,
)
from observelens_service.modules.incidents.service import (
    MAX_INTEGRATION_ID,
    MIN_INTEGRATION_ID,
    IncidentService,
)

router = APIRouter(prefix="/incidents", tags=["Incident"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[IncidentService]:
    async with session_scope(factory) as session:
        yield IncidentService(session)


ServiceDependency = Annotated[IncidentService, Depends(get_service)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]
IntegrationIdPath = Annotated[int, Path(ge=MIN_INTEGRATION_ID, le=MAX_INTEGRATION_ID)]


def enum_option(value: str) -> dict[str, str]:
    return {"value": value, "label": value.upper()}


@router.get("", response_model=IncidentPage)
async def list_incidents(
    context: ContextDependency,
    service: ServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    status: str | None = None,
    source: str | None = None,
    name: str | None = None,
) -> IncidentPage:
    return await service.list(context, page, page_size, severity, status, source, name)


@router.get("/severities")
async def list_severities(context: ContextDependency) -> list[dict[str, str]]:
    return [enum_option(value) for value in SUPPORTED_INCIDENT_SEVERITIES]


@router.get("/statuses")
async def list_statuses(context: ContextDependency) -> list[dict[str, str]]:
    return [enum_option(value) for value in SUPPORTED_INCIDENT_STATUSES]


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


@router.post("/{incident_id:int}/transition", response_model=IncidentResponse)
async def transition_incident(
    incident_id: int,
    request: TransitionRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> IncidentResponse:
    return await service.transition_status(context, incident_id, request.status, request.assignee)


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
    context: ContextDependency,
    service: ServiceDependency,
    integration_type: Annotated[IntegrationType | None, Query(alias="type")] = None,
    status: IntegrationStatus | None = None,
    name: str | None = None,
) -> list[IncidentIntegrationResponse]:
    return await service.list_integrations(context, integration_type, status, name)


@router.post("/integrations", response_model=IncidentIntegrationResponse, status_code=201)
async def create_integration(
    request: IntegrationCreateRequest, context: ContextDependency, service: ServiceDependency
) -> IncidentIntegrationResponse:
    return await service.create_integration(context, request)


@router.get("/integrations/types")
async def list_integration_types(context: ContextDependency) -> list[dict[str, str]]:
    return [enum_option(value) for value in SUPPORTED_INTEGRATION_TYPES]


@router.get("/integrations/statuses")
async def list_integration_statuses(context: ContextDependency) -> list[dict[str, str]]:
    return [enum_option(value) for value in ("Enabled", "Disabled")]


@router.post(
    "/integrations/Webhook/{integration_id:int}/webhook",
    response_model=IncidentResponse,
    status_code=201,
)
async def receive_webhook_incident(
    integration_id: IntegrationIdPath, request: WebhookIncidentRequest, service: ServiceDependency
) -> IncidentResponse:
    return await service.create_from_webhook(integration_id, request)


@router.post(
    "/integrations/Alertmanager/{integration_id:int}/webhook",
    response_model=IncidentResponse,
    status_code=201,
)
async def receive_alertmanager_incident(
    integration_id: IntegrationIdPath,
    request: AlertmanagerWebhookRequest,
    service: ServiceDependency,
) -> IncidentResponse:
    return await service.create_from_alertmanager(integration_id, request)


@router.get("/integrations/{integration_id}", response_model=IncidentIntegrationResponse)
async def get_integration(
    integration_id: IntegrationIdPath, context: ContextDependency, service: ServiceDependency
) -> IncidentIntegrationResponse:
    return await service.get_integration(context, integration_id)


@router.patch("/integrations/{integration_id}", response_model=IncidentIntegrationResponse)
async def update_integration(
    integration_id: IntegrationIdPath,
    request: IntegrationUpdateRequest,
    context: ContextDependency,
    service: ServiceDependency,
) -> IncidentIntegrationResponse:
    return await service.update_integration(context, integration_id, request)


@router.delete("/integrations/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: IntegrationIdPath, context: ContextDependency, service: ServiceDependency
) -> Response:
    await service.delete_integration(context, integration_id)
    return Response(status_code=204)
