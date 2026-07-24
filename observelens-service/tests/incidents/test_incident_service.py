from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context
from observelens_service.common.exceptions import ResourceAlreadyExistsError
from observelens_service.config.settings import get_settings
from observelens_service.modules.incidents.models import IncidentIntegrationModel
from observelens_service.modules.incidents.router import get_service
from observelens_service.modules.incidents.schemas import (
    IncidentIntegrationResponse,
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
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
                    "id": 1784859290458401,
                    "name": "test5",
                    "type": "Webhook",
                    "status": "ENABLED",
                    "webhook_url": "/api/v1/incidents/integrations/1784859290458401/webhook",
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
        params={"type": "Grafana", "status": "ENABLED", "name": "prod"},
    )

    assert response.status_code == 200
    assert service.filters == ("Grafana", "ENABLED", "prod")


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
        json={"name": "Grafana prod", "type": "Grafana", "status": "ENABLED"},
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
        {"value": "Webhook", "label": "Webhook"},
        {"value": "AlertManager", "label": "AlertManager"},
        {"value": "Grafana", "label": "Grafana"},
        {"value": "Prometheus", "label": "Prometheus"},
        {"value": "Datadog", "label": "Datadog"},
        {"value": "Zabbix", "label": "Zabbix"},
        {"value": "Nagios", "label": "Nagios"},
        {"value": "OpsGenie", "label": "OpsGenie"},
    ]


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
        {"value": "ENABLED", "label": "Enabled"},
        {"value": "DISABLED", "label": "Disabled"},
    ]


@pytest.mark.asyncio
async def test_create_integration_persists_type(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    captured: list[IncidentIntegrationModel] = []
    monkeypatch.setattr(service._repository, "add", captured.append)
    monkeypatch.setattr(service._repository, "get_integration_by_name", _no_existing_integration)

    response = await service.create_integration(
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
        IntegrationCreateRequest(name="Grafana prod", type="Grafana"),
    )

    assert response.type == "Grafana"
    assert captured[0].type == "Grafana"
    assert captured[0].status == "ENABLED"
    assert captured[0].tenant_id == 7
    assert response.token == captured[0].token
    assert response.token_hint == f"****{response.token[-8:]}"


async def _no_existing_integration(tenant_id: int, name: str) -> IncidentIntegrationModel | None:
    return None


@pytest.mark.asyncio
async def test_create_integration_rejects_duplicate_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    existing = IncidentIntegrationModel(
        id=101,
        tenant_id=7,
        name="Grafana prod",
        type="Grafana",
        status="ENABLED",
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

    with pytest.raises(ResourceAlreadyExistsError) as exc_info:
        await service.create_integration(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            IntegrationCreateRequest(name="Grafana prod", type="Grafana"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RESOURCE_ALREADY_EXISTS"
    assert "Grafana prod" in exc_info.value.message


@pytest.mark.asyncio
async def test_create_integration_maps_database_duplicate_to_already_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = IncidentService(DuplicateFlushSession())  # type: ignore[arg-type]
    monkeypatch.setattr(service._repository, "get_integration_by_name", _no_existing_integration)

    with pytest.raises(ResourceAlreadyExistsError) as exc_info:
        await service.create_integration(
            RequestContext(tenant_id=7, user_id=11, request_id="req-1"),
            IntegrationCreateRequest(name="Grafana prod", type="Grafana"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RESOURCE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_update_integration_can_toggle_status(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    integration = IncidentIntegrationModel(
        id=101,
        tenant_id=7,
        name="Webhook prod",
        type="Webhook",
        status="ENABLED",
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
        101,
        IntegrationUpdateRequest(status="DISABLED"),
    )

    assert response.status == "DISABLED"
    assert integration.status == "DISABLED"


@pytest.mark.asyncio
async def test_delete_integration_marks_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    service = IncidentService(FakeSession())  # type: ignore[arg-type]
    now = datetime.now(UTC)
    integration = IncidentIntegrationModel(
        id=101,
        tenant_id=7,
        name="Webhook prod",
        type="Webhook",
        status="ENABLED",
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
        RequestContext(tenant_id=7, user_id=11, request_id="req-1"), 101
    )

    assert isinstance(integration.delete_time, datetime)
