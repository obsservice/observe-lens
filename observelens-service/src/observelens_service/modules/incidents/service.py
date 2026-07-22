import builtins
import secrets
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.common.context import RequestContext
from observelens_service.common.exceptions import ResourceNotFoundError
from observelens_service.modules.conversations.models import ConversationModel
from observelens_service.modules.conversations.service import new_id
from observelens_service.modules.incidents.models import IncidentIntegrationModel, IncidentModel
from observelens_service.modules.incidents.repository import IncidentRepository
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


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = IncidentRepository(session)

    async def list(
        self,
        context: RequestContext,
        page: int,
        page_size: int,
        severity: str | None,
        status: str | None,
    ) -> IncidentPage:
        items, total = await self._repository.list(
            context.tenant_id, page, page_size, severity, status
        )
        return IncidentPage(
            items=[IncidentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create(
        self, context: RequestContext, request: IncidentCreateRequest
    ) -> IncidentResponse:
        incident = IncidentModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            incident_id=f"INC-{new_id()}",
            title=request.title,
            description=request.description,
            severity=request.severity,
            status="OPEN",
            source=request.source,
            external_metadata=request.external_metadata,
            started_time=request.started_at,
            create_by=context.user_id,
        )
        self._repository.add(incident)
        await self._session.flush()
        return IncidentResponse.model_validate(incident)

    async def get(self, context: RequestContext, incident_id: int) -> IncidentResponse:
        return IncidentResponse.model_validate(await self._require(context, incident_id))

    async def update(
        self, context: RequestContext, incident_id: int, request: IncidentUpdateRequest
    ) -> IncidentResponse:
        incident = await self._require(context, incident_id)
        for field in ("title", "description", "severity", "status"):
            value = getattr(request, field)
            if value is not None:
                setattr(incident, field, value)
        incident.update_by = context.user_id
        await self._session.flush()
        return IncidentResponse.model_validate(incident)

    async def delete(self, context: RequestContext, incident_id: int) -> None:
        incident = await self._require(context, incident_id)
        incident.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def archive(self, context: RequestContext, incident_id: int) -> IncidentResponse:
        incident = await self._require(context, incident_id)
        incident.status = "ARCHIVED"
        incident.update_by = context.user_id
        await self._session.flush()
        return IncidentResponse.model_validate(incident)

    async def open_conversation(
        self, context: RequestContext, incident_id: int
    ) -> OpenConversationResponse:
        incident = await self._require(context, incident_id)
        if incident.conversation_id is None:
            conversation = ConversationModel(
                id=new_id(),
                tenant_id=context.tenant_id,
                owner_id=context.user_id,
                title=incident.title,
                status="ACTIVE",
                create_time=datetime.now(UTC),
                update_time=datetime.now(UTC),
            )
            self._session.add(conversation)
            incident.conversation_id = conversation.id
            incident.status = "INVESTIGATING"
            await self._session.flush()
        return OpenConversationResponse(conversation_id=incident.conversation_id)

    async def list_integrations(
        self, context: RequestContext
    ) -> builtins.list[IncidentIntegrationResponse]:
        integrations = await self._repository.list_integrations(context.tenant_id)
        return [self._integration_response(item) for item in integrations]

    async def create_integration(
        self, context: RequestContext, request: IntegrationCreateRequest
    ) -> IncidentIntegrationResponse:
        integration = IncidentIntegrationModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            name=request.name,
            status=request.status,
            token_hint=f"****{secrets.token_hex(4)}",
        )
        self._repository.add(integration)
        await self._session.flush()
        return self._integration_response(integration)

    async def get_integration(
        self, context: RequestContext, integration_id: int
    ) -> IncidentIntegrationResponse:
        return self._integration_response(await self._require_integration(context, integration_id))

    async def update_integration(
        self, context: RequestContext, integration_id: int, request: IntegrationUpdateRequest
    ) -> IncidentIntegrationResponse:
        integration = await self._require_integration(context, integration_id)
        if request.name is not None:
            integration.name = request.name
        if request.status is not None:
            integration.status = request.status
        await self._session.flush()
        return self._integration_response(integration)

    async def delete_integration(self, context: RequestContext, integration_id: int) -> None:
        integration = await self._require_integration(context, integration_id)
        integration.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def _require(self, context: RequestContext, incident_id: int) -> IncidentModel:
        incident = await self._repository.get(context.tenant_id, incident_id)
        if incident is None:
            raise ResourceNotFoundError("Incident")
        return incident

    async def _require_integration(
        self, context: RequestContext, integration_id: int
    ) -> IncidentIntegrationModel:
        integration = await self._repository.get_integration(context.tenant_id, integration_id)
        if integration is None:
            raise ResourceNotFoundError("Incident integration")
        return integration

    @staticmethod
    def _integration_response(integration: IncidentIntegrationModel) -> IncidentIntegrationResponse:
        response = IncidentIntegrationResponse.model_validate(integration)
        return response.model_copy(
            update={"webhook_url": f"/api/v1/incidents/integrations/{integration.id}/webhook"}
        )
