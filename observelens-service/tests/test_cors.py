from fastapi.testclient import TestClient

from observelens_service.config.settings import get_settings


def test_cors_preflight_for_api_routes(monkeypatch) -> None:
    monkeypatch.setenv(
        "OBSERVELENS_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens",
    )
    monkeypatch.setenv("OBSERVELENS_SERVICE_AGENT_BASE_URL", "http://localhost:3082")
    monkeypatch.setenv("OBSERVELENS_SERVICE_CORS_ALLOWED_ORIGINS", "http://localhost:3080")
    get_settings.cache_clear()

    from observelens_service.main import create_app

    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/api/v1/incidents/integrations",
        headers={
            "Origin": "http://localhost:3080",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3080"
