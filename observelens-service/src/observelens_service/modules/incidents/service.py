import builtins
import secrets
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.common.context import RequestContext
from observelens_service.common.exceptions import (
    InvalidRequestError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from observelens_service.modules.conversations.models import ConversationModel
from observelens_service.modules.conversations.service import new_id
from observelens_service.modules.incidents.models import IncidentIntegrationModel, IncidentModel
from observelens_service.modules.incidents.repository import IncidentRepository
from observelens_service.modules.incidents.schemas import (
    TRANSITION_RULES,
    AlertmanagerWebhookRequest,
    IncidentIntegrationResponse,
    IncidentPage,
    IncidentResponse,
    IncidentUpdateRequest,
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    OpenConversationResponse,
    WebhookIncidentRequest,
)

MIN_INTEGRATION_ID = 10_000_000
MAX_INTEGRATION_ID = 99_999_999
INTEGRATION_ID_RANGE = MAX_INTEGRATION_ID - MIN_INTEGRATION_ID + 1
INTEGRATION_ID_RETRY_LIMIT = 5


def new_integration_id() -> int:
    return MIN_INTEGRATION_ID + secrets.randbelow(INTEGRATION_ID_RANGE)


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
        source: str | None,
        name: str | None,
    ) -> IncidentPage:
        items, total = await self._repository.list(
            context.tenant_id, page, page_size, severity, status, source, name
        )
        return IncidentPage(
            items=[IncidentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )


    async def create_from_webhook(
        self, integration_id: int, request: WebhookIncidentRequest
    ) -> IncidentResponse:
        integration = await self._require_webhook_integration("Webhook", integration_id)
        incident = self._build_incident(
            tenant_id=integration.tenant_id,
            title=request.title,
            description=request.description,
            severity=request.severity,
            source=self._incident_source(integration, request.source),
            started_at=request.started_at,
            external_metadata=request.labels,
        )
        self._repository.add(incident)
        await self._session.flush()
        return IncidentResponse.model_validate(incident)

    async def create_from_alertmanager(
        self, integration_id: int, request: AlertmanagerWebhookRequest
    ) -> IncidentResponse:
        integration = await self._require_webhook_integration("Alertmanager", integration_id)
        first_alert = request.alerts[0] if request.alerts else None
        annotations = first_alert.annotations if first_alert else request.commonAnnotations
        labels = first_alert.labels if first_alert else request.commonLabels
        title = (
            annotations.get("summary")
            or labels.get("alertname")
            or request.commonLabels.get("alertname")
            or "Alertmanager alert"
        )
        description = annotations.get("description") or request.externalURL
        started_at = first_alert.startsAt if first_alert else None
        incident = self._build_incident(
            tenant_id=integration.tenant_id,
            title=title,
            description=description,
            severity=self._alertmanager_severity(labels),
            source=self._incident_source(integration, request.source),
            started_at=started_at,
            external_metadata={
                "receiver": request.receiver or "",
                "status": request.status or "",
                "external_url": request.externalURL or "",
                **request.commonLabels,
                **labels,
            },
            status="Resolved" if request.status == "resolved" else "Open",
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
        incident.status = "Archived"
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
            incident.status = "Investigating"
            await self._session.flush()
        return OpenConversationResponse(conversation_id=incident.conversation_id)

    async def transition_status(
        self, context: RequestContext, incident_id: int, target_status: str, assignee: str | None = None
    ) -> IncidentResponse:
        incident = await self._require(context, incident_id)
        allowed = TRANSITION_RULES.get(incident.status, [])
        if target_status not in allowed:
            raise InvalidRequestError(
                f'Cannot transition from "{incident.status}" to "{target_status}"'
            )
        if target_status == "Acknowledged":
            if not assignee:
                raise InvalidRequestError('"assignee" is required when transitioning to Acknowledged')
            metadata = dict(incident.external_metadata)
            metadata["assignee"] = assignee
            incident.external_metadata = metadata
        incident.status = target_status
        incident.update_by = context.user_id
        await self._session.flush()
        return IncidentResponse.model_validate(incident)

    async def list_integrations(
        self,
        context: RequestContext,
        integration_type: str | None,
        status: str | None,
        name: str | None,
    ) -> builtins.list[IncidentIntegrationResponse]:
        integrations = await self._repository.list_integrations(
            context.tenant_id, integration_type, status, name
        )
        return [self._integration_response(item) for item in integrations]

    async def create_integration(
        self, context: RequestContext, request: IntegrationCreateRequest
    ) -> IncidentIntegrationResponse:
        existing = await self._repository.get_integration_by_name(context.tenant_id, request.name)
        if existing is not None:
            raise ResourceAlreadyExistsError("Incident integration", "name", request.name)

        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        integration = IncidentIntegrationModel(
            id=await self._new_unique_integration_id(),
            tenant_id=context.tenant_id,
            name=request.name,
            type=request.type,
            status=request.status,
            token=token,
            token_hint=f"****{token[-8:]}",
            create_time=now,
            update_time=now,
        )
        self._repository.add(integration)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if self._is_duplicate_integration_name(exc):
                raise ResourceAlreadyExistsError(
                    "Incident integration", "name", request.name
                ) from exc
            raise
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
        if request.type is not None:
            integration.type = request.type
        if request.status is not None:
            integration.status = request.status
        integration.update_time = datetime.now(UTC)
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

    async def _new_unique_integration_id(self) -> int:
        for _ in range(INTEGRATION_ID_RETRY_LIMIT):
            integration_id = new_integration_id()
            existing = await self._repository.get_integration_by_id(integration_id)
            if existing is None:
                return integration_id
        raise ResourceAlreadyExistsError("Incident integration", "id", "8-digit id space")

    @staticmethod
    def _integration_response(integration: IncidentIntegrationModel) -> IncidentIntegrationResponse:
        response = IncidentIntegrationResponse.model_validate(integration)
        return response.model_copy(
            update={
                "webhook_url": (
                    f"/api/v1/incidents/integrations/{integration.type}/{integration.id}/webhook"
                )
            }
        )

    @staticmethod
    def _incident_source(integration: IncidentIntegrationModel, request_source: str | None) -> str:
        source = request_source.strip() if request_source is not None else ""
        if not source:
            return integration.name
        if source != integration.name:
            raise InvalidRequestError(
                f'source "{source}" does not match integration "{integration.name}"'
            )
        return source

    @staticmethod
    def _is_duplicate_integration_name(exc: IntegrityError) -> bool:
        message = str(exc.orig)
        return (
            "uq_incident_integration_tenant_name" in message
            or "t_incident_integrations_tenant_id_name_key" in message
        )

    async def _require_webhook_integration(
        self, integration_type: str, integration_id: int
    ) -> IncidentIntegrationModel:
        integration = await self._repository.get_integration_for_webhook(
            integration_type, integration_id
        )
        if integration is None:
            raise ResourceNotFoundError("Incident integration")
        return integration

    @staticmethod
    def _build_incident(
        tenant_id: int,
        title: str,
        description: str | None,
        severity: str,
        source: str,
        started_at: datetime | None,
        external_metadata: dict[str, str],
        status: str = "Open",
    ) -> IncidentModel:
        now = datetime.now(UTC)
        return IncidentModel(
            id=new_id(),
            tenant_id=tenant_id,
            incident_id=f"INC-{new_id()}",
            title=title,
            description=description,
            severity=severity,
            status=status,
            source=source,
            external_metadata=external_metadata,
            started_time=started_at,
            create_by=0,
            create_time=now,
            update_time=now,
        )

    @staticmethod
    def _alertmanager_severity(labels: dict[str, str]) -> str:
        severity = labels.get("severity", "").lower()
        if severity == "critical":
            return "Critical"
        if severity in {"error", "err"}:
            return "Error"
        return "Warn"
