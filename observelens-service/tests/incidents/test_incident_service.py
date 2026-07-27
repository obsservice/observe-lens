from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context
from observelens_service.common.exceptions import InvalidRequestError, ResourceAlreadyExistsError
from observelens_service.config.settings import get_settings
from observelens_service.modules.incidents.models import IncidentIntegrationModel, IncidentModel
from observelens_service.modules.incidents.router import get_service
from observelens_service.modules.incidents.schemas import (
    AlertmanagerWebhookRequest,
    IncidentIntegrationResponse,
    IncidentPage,
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    WebhookIncidentRequest,
)
from observelens_service.modules.incidents.service import IncidentService


class FakeSession:
    async def flush(self) -> None:
        return None


class DuplicateFlushSession:
    def add(self, item: object) -> None:
        return None

    async def flush(self) -> None:
        raise IntegrityError(
            statement="INSERT INTO t_incident_integrations ...",
            params={},
            orig=RuntimeError("uq_incident_integration_tenant_name"),
        )


class FakeIntegrationService:
    filters: tuple[str | None, str | None, str | None] | None = None

    async def list_integrations(
        self,
        context: RequestContext,
        integration_type: str | None,
        status: str | None,
        name: str | None,
    ) -> list[IncidentIntegrationResponse]:
        self.filters = (integration_type, status, name)
        now = datetime.now(UTC)
        return [
            IncidentIntegrationResponse.model_validate(
                {
                    "id": 12345678,
                    "name": "test5",
                    "type": "Webhook",
                    "status": "Enabled",
                    "webhook_url": ("/api/v1/incidents/integrations/Webhook/12345678/webhook"),
                    "token": "plain-token-418b20b0",
                    "token_hint": "****418b20b0",
                    "create_time": now,
                    "update_time": now,
                }
            )
        ]


class DuplicateIntegrationService:
    async def create_integration(
        self, context: RequestContext, request: IntegrationCreateRequest
    ) -> IncidentIntegrationResponse:
        raise ResourceAlreadyExistsError("Incident integration", "name", request.name)


class FakeIncidentListService:
    filters: tuple[str | None, str | None, str | None, str | None] | None = None

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
        self.filters = (severity, status, source, name)
        return IncidentPage(items=[], total=0, page=page, page_size=page_size)


def test_list_incidents_passes_source_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeIncidentListService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/incidents",
        params={"severity": "Error", "status": "Open", "source": "Alertmanager"},
    )

    assert response.status_code == 200
    assert service.filters == ("Error", "Open", "Alertmanager", None)


def test_create_incident_endpoint_is_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.post(
        "/api/v1/incidents",
        json={"title": "CPU high", "severity": "Warn"},
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 405


def test_list_integrations_response_includes_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeIntegrationService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.get("/api/v1/incidents/integrations")

    assert response.status_code == 200
    assert response.json()[0]["type"] == "Webhook"
    assert response.json()[0]["token"] == "plain-token-418b20b0"
    assert service.filters == (None, None, None)


def test_list_integrations_passes_filter_params(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeIntegrationService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/incidents/integrations",
        params={"type": "Alertmanager", "status": "Enabled", "name": "prod"},
    )

    assert response.status_code == 200
    assert service.filters == ("Alertmanager", "Enabled", "prod")


def test_create_integration_duplicate_name_returns_already_exists_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    app.dependency_overrides[get_service] = lambda: DuplicateIntegrationService()
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/incidents/integrations",
        json={"name": "Alertmanager prod", "type": "Alertmanager", "status": "Enabled"},
        headers={"X-Request-Id": "req-1"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "RESOURCE_ALREADY_EXISTS"
    assert response.json()["request_id"] == "req-1"


def test_list_integration_types_returns_supported_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/incidents/integrations/types",
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"value": "Webhook", "label": "WEBHOOK"},
        {"value": "Alertmanager", "label": "ALERTMANAGER"},
    ]


def test_list_incident_sources_endpoint_is_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/incidents/sources",
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 404


def test_list_integration_statuses_returns_supported_statuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/incidents/integrations/statuses",
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"value": "Enabled", "label": "ENABLED"},
        {"value": "Disabled", "label": "DISABLED"},
    ]


def test_list_incident_statuses_returns_supported_statuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/incidents/statuses",
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"value": "Open", "label": "OPEN"},
        {"value": "Acknowledged", "label": "ACKNOWLEDGED"},
        {"value": "Investigating", "label": "INVESTIGATING"},
        {"value": "Recovering", "label": "RECOVERING"},
        {"value": "Resolved", "label": "RESOLVED"},
        {"value": "Closed", "label": "CLOSED"},
        {"value": "Archived", "label": "ARCHIVED"},
    ]


def test_list_incident_severities_returns_supported_severities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/incidents/severities",
        headers={"X-Tenant-Id": "7", "X-User-Id": "11"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"value": "Critical", "label": "CRITICAL"},
        {"value": "Error", "label": "ERROR"},
        {"value": "Warn", "label": "WARN"},
    ]


@pytest.mark.asyncio
async def test_create_integration_persists_type(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    captured: list[IncidentIntegrationModel] = []
    monkeypatch.setattr(service._repository, "add", captured.append)
    monkeypatch.setattr(service._repository, "get_integration_by_name", _no_existing_integration)
    monkeypatch.setattr(service._repository, "get_integration_by_id", _no_existing_integration_id)

    response = await service.create_integration(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        IntegrationCreateRequest(name="Alertmanager prod", type="Alertmanager"),
    )

    assert response.type == "Alertmanager"
    assert 10_000_000 <= response.id <= 99_999_999
    assert captured[0].type == "Alertmanager"
    assert captured[0].status == "Enabled"
    assert captured[0].tenant_id == 7
    assert response.token == captured[0].token
    assert response.token_hint == f"****{response.token[-8:]}"


async def _no_existing_integration(tenant_id: int, name: str) -> IncidentIntegrationModel | None:
    return None


async def _no_existing_integration_id(integration_id: int) -> IncidentIntegrationModel | None:
    return None


@pytest.mark.asyncio
async def test_create_integration_rejects_duplicate_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    existing = IncidentIntegrationModel(
        id=12345678,
        tenant_id=7,
        name="Alertmanager prod",
        type="Alertmanager",
        status="Enabled",
        token="plain-token-abcd",
        token_hint="****abcd",
        create_time=now,
        update_time=now,
    )

    async def get_integration_by_name(tenant_id: int, name: str) -> IncidentIntegrationModel | None:
        return existing

    monkeypatch.setattr(
        service._repository,
        "get_integration_by_name",
        get_integration_by_name,
    )
    monkeypatch.setattr(service._repository, "get_integration_by_id", _no_existing_integration_id)

    with pytest.raises(ResourceAlreadyExistsError) as exc_info:
        await service.create_integration(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            IntegrationCreateRequest(name="Alertmanager prod", type="Alertmanager"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RESOURCE_ALREADY_EXISTS"
    assert "Alertmanager prod" in exc_info.value.message


@pytest.mark.asyncio
async def test_create_integration_maps_database_duplicate_to_already_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(DuplicateFlushSession())  # type: ignore[arg-type]
    monkeypatch.setattr(service._repository, "get_integration_by_name", _no_existing_integration)
    monkeypatch.setattr(service._repository, "get_integration_by_id", _no_existing_integration_id)

    with pytest.raises(ResourceAlreadyExistsError) as exc_info:
        await service.create_integration(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            IntegrationCreateRequest(name="Alertmanager prod", type="Alertmanager"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RESOURCE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_from_webhook_uses_integration_tenant_and_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    captured: list[IncidentModel] = []
    integration = _integration_model(integration_type="Webhook")

    async def get_integration_for_webhook(
        integration_type: str, integration_id: int
    ) -> IncidentIntegrationModel | None:
        assert integration_type == "Webhook"
        assert integration_id == 12345678
        return integration

    monkeypatch.setattr(service._repository, "add", captured.append)
    monkeypatch.setattr(
        service._repository,
        "get_integration_for_webhook",
        get_integration_for_webhook,
    )

    response = await service.create_from_webhook(
        12345678,
        WebhookIncidentRequest(
            title="CPU high",
            description="pod cpu is high",
            severity="Error",
            source=" ",
            labels={"service": "checkout"},
        ),
    )

    assert response.name == "CPU high"
    assert response.severity == "Error"
    assert response.status == "Open"
    assert response.source == "Webhook prod"
    assert captured[0].tenant_id == 7
    assert captured[0].external_metadata == {"service": "checkout"}


@pytest.mark.asyncio
async def test_create_from_alertmanager_maps_alert_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    captured: list[IncidentModel] = []
    integration = _integration_model(integration_type="Alertmanager")

    async def get_integration_for_webhook(
        integration_type: str, integration_id: int
    ) -> IncidentIntegrationModel | None:
        assert integration_type == "Alertmanager"
        assert integration_id == 12345678
        return integration

    monkeypatch.setattr(service._repository, "add", captured.append)
    monkeypatch.setattr(
        service._repository,
        "get_integration_for_webhook",
        get_integration_for_webhook,
    )

    response = await service.create_from_alertmanager(
        12345678,
        AlertmanagerWebhookRequest.model_validate(
            {
                "receiver": "observe-lens",
                "status": "firing",
                "externalURL": "http://alertmanager.example",
                "alerts": [
                    {
                        "labels": {"alertname": "PodCrashLoop", "severity": "critical"},
                        "annotations": {
                            "summary": "Pod crash loop",
                            "description": "checkout pod is restarting",
                        },
                    }
                ],
            }
        ),
    )

    assert response.name == "Pod crash loop"
    assert response.description == "checkout pod is restarting"
    assert response.severity == "Critical"
    assert response.status == "Open"
    assert response.source == "Alertmanager prod"
    assert captured[0].tenant_id == 7
    assert captured[0].external_metadata["receiver"] == "observe-lens"


@pytest.mark.asyncio
async def test_create_from_webhook_accepts_matching_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    integration = _integration_model(integration_type="Webhook")
    captured: list[IncidentModel] = []

    async def get_integration_for_webhook(
        integration_type: str, integration_id: int
    ) -> IncidentIntegrationModel | None:
        return integration

    monkeypatch.setattr(service._repository, "add", captured.append)
    monkeypatch.setattr(
        service._repository,
        "get_integration_for_webhook",
        get_integration_for_webhook,
    )

    response = await service.create_from_webhook(
        12345678,
        WebhookIncidentRequest(title="CPU high", source="Webhook prod"),
    )

    assert response.source == "Webhook prod"
    assert captured[0].source == "Webhook prod"


@pytest.mark.asyncio
async def test_create_from_webhook_rejects_mismatched_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    integration = _integration_model(integration_type="Webhook")

    async def get_integration_for_webhook(
        integration_type: str, integration_id: int
    ) -> IncidentIntegrationModel | None:
        return integration

    monkeypatch.setattr(
        service._repository,
        "get_integration_for_webhook",
        get_integration_for_webhook,
    )

    with pytest.raises(InvalidRequestError) as exc_info:
        await service.create_from_webhook(
            12345678,
            WebhookIncidentRequest(title="CPU high", source="Wrong source"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "INVALID_REQUEST"


def _integration_model(integration_type: str) -> IncidentIntegrationModel:
    now = datetime.now(UTC)
    return IncidentIntegrationModel(
        id=12345678,
        tenant_id=7,
        name=f"{integration_type} prod",
        type=integration_type,
        status="Enabled",
        token="plain-token-abcd",
        token_hint="****abcd",
        create_time=now,
        update_time=now,
    )


@pytest.mark.asyncio
async def test_update_integration_can_toggle_status(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    integration = IncidentIntegrationModel(
        id=12345678,
        tenant_id=7,
        name="Webhook prod",
        type="Webhook",
        status="Enabled",
        token="plain-token-abcd",
        token_hint="****abcd",
        create_time=now,
        update_time=now,
    )

    async def get_integration(tenant_id: int, integration_id: int) -> IncidentIntegrationModel:
        return integration

    monkeypatch.setattr(
        service._repository,
        "get_integration",
        get_integration,
    )

    response = await service.update_integration(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        12345678,
        IntegrationUpdateRequest(status="Disabled"),
    )

    assert response.status == "Disabled"
    assert integration.status == "Disabled"


@pytest.mark.asyncio
async def test_delete_integration_marks_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    integration = IncidentIntegrationModel(
        id=12345678,
        tenant_id=7,
        name="Webhook prod",
        type="Webhook",
        status="Enabled",
        token="plain-token-abcd",
        token_hint="****abcd",
        create_time=now,
        update_time=now,
    )

    async def get_integration(tenant_id: int, integration_id: int) -> IncidentIntegrationModel:
        return integration

    monkeypatch.setattr(
        service._repository,
        "get_integration",
        get_integration,
    )

    await service.delete_integration(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"), 12345678
    )

    assert isinstance(integration.delete_time, datetime)


def test_transition_incident_valid_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeTransitionService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/incidents/1/transition",
        json={"status": "Investigating"},
    )

    assert response.status_code == 200
    assert service.last_transition == "Investigating"
    assert service.last_assignee is None


def test_transition_incident_invalid_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeInvalidTransitionService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/incidents/1/transition",
        json={"status": "Closed"},
    )

    assert response.status_code == 400


class FakeTransitionService:
    last_transition: str | None = None
    last_assignee: str | None = None

    async def transition_status(
        self, context: RequestContext, incident_id: int, target_status: str, assignee: str | None = None
    ) -> IncidentModel:
        self.last_assignee = assignee
        self.last_transition = target_status
        now = datetime.now(UTC)
        return IncidentModel(
            id=1,
            tenant_id=7,
            incident_id="INC-12345678",
            title="Test incident",
            description=None,
            severity="Warn",
            status=target_status,
            source="Webhook",
            external_metadata={},
            conversation_id=None,
            started_time=None,
            create_by=11,
            update_by=None,
            create_time=now,
            update_time=now,
        )


class FakeInvalidTransitionService:
    async def transition_status(
        self, context: RequestContext, incident_id: int, target_status: str, assignee: str | None = None
    ) -> None:
        raise InvalidRequestError(
            f'Cannot transition from "Open" to "{target_status}"'
        )


def test_transition_to_acknowledged_requires_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    service = FakeTransitionService()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=7, user_id=11, request_id="req-1"
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/incidents/1/transition",
        json={"status": "Acknowledged", "assignee": "zhangsan"},
    )

    assert response.status_code == 200
    assert service.last_transition == "Acknowledged"
    assert service.last_assignee == "zhangsan"


@pytest.mark.asyncio
async def test_transition_status_valid_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    incident = IncidentModel(
        id=1,
        tenant_id=7,
        incident_id="INC-123456789",
        title="Test incident",
        description=None,
        severity="Warn",
        status="Open",
        source="Webhook",
        external_metadata={},
        started_time=now,
        create_by=11,
        update_by=None,
        create_time=now,
        update_time=now,
    )

    async def require(ctx: RequestContext, incident_id: int) -> IncidentModel:
        return incident

    monkeypatch.setattr(service, "_require", require)

    response = await service.transition_status(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        1,
        "Investigating",
    )

    assert incident.status == "Investigating"
    assert incident.update_by == 11
    assert response.status == "Investigating"


@pytest.mark.asyncio
async def test_transition_status_rejects_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    incident = IncidentModel(
        id=1,
        tenant_id=7,
        incident_id="INC-123456789",
        title="Test incident",
        description=None,
        severity="Warn",
        status="Open",
        source="Webhook",
        external_metadata={},
        started_time=now,
        create_by=11,
        update_by=None,
        create_time=now,
        update_time=now,
    )

    async def require(ctx: RequestContext, incident_id: int) -> IncidentModel:
        return incident

    monkeypatch.setattr(service, "_require", require)

    with pytest.raises(InvalidRequestError) as exc_info:
        await service.transition_status(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            1,
            "Closed",
        )

    assert exc_info.value.status_code == 400
    assert "Cannot transition" in exc_info.value.message
    assert incident.status == "Open"


@pytest.mark.asyncio
async def test_transition_to_acknowledged_missing_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    incident = IncidentModel(
        id=1,
        tenant_id=7,
        incident_id="INC-123456789",
        title="Test incident",
        description=None,
        severity="Warn",
        status="Open",
        source="Webhook",
        external_metadata={},
        started_time=now,
        create_by=11,
        update_by=None,
        create_time=now,
        update_time=now,
    )

    async def require(ctx: RequestContext, incident_id: int) -> IncidentModel:
        return incident

    monkeypatch.setattr(service, "_require", require)

    with pytest.raises(InvalidRequestError) as exc_info:
        await service.transition_status(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            1,
            "Acknowledged",
        )

    assert exc_info.value.status_code == 400
    assert "assignee" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_transition_to_acknowledged_stores_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    incident = IncidentModel(
        id=1,
        tenant_id=7,
        incident_id="INC-123456789",
        title="Test incident",
        description=None,
        severity="Warn",
        status="Open",
        source="Webhook",
        external_metadata={},
        started_time=now,
        create_by=11,
        update_by=None,
        create_time=now,
        update_time=now,
    )

    async def require(ctx: RequestContext, incident_id: int) -> IncidentModel:
        return incident

    monkeypatch.setattr(service, "_require", require)

    response = await service.transition_status(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        1,
        "Acknowledged",
        "wangwei",
    )

    assert incident.status == "Acknowledged"
    assert incident.external_metadata.get("assignee") == "wangwei"
    assert response.status == "Acknowledged"


@pytest.mark.asyncio
async def test_transition_status_from_closed_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    incident = IncidentModel(
        id=1,
        tenant_id=7,
        incident_id="INC-123456789",
        title="Test incident",
        description=None,
        severity="Warn",
        status="Closed",
        source="Webhook",
        external_metadata={},
        started_time=now,
        create_by=11,
        update_by=None,
        create_time=now,
        update_time=now,
    )

    async def require(ctx: RequestContext, incident_id: int) -> IncidentModel:
        return incident

    monkeypatch.setattr(service, "_require", require)

    with pytest.raises(InvalidRequestError) as exc_info:
        await service.transition_status(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            1,
            "Resolved",
        )

    assert incident.status == "Closed"
