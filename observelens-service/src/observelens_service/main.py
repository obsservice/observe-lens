from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from observelens_service.api import api_router
from observelens_service.common.exceptions import DomainError, domain_error_handler
from observelens_service.config.settings import get_settings
from observelens_service.database.session import build_session_factory

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.session_factory = build_session_factory(settings)
    logger.info("service_started", environment=settings.environment)
    yield
    logger.info("service_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ObserveLens API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.openapi = lambda: build_openapi_schema(app)  # type: ignore[method-assign]

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", request_id=request.headers.get("x-request-id", ""))
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": request.headers.get("x-request-id", ""),
                "details": {},
            },
        )

    return app


def build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )
    tags = schema.setdefault("tags", [])
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict) and tag.get("name") == "Knowledge":
                tag["description"] = (
                    "Knowledge requests are proxied to observelens-knowledge-base. "
                    "For concrete Knowledge API request and response contracts, see "
                    "openapi/observelens-knowledge-base/openapi.yaml."
                )
                tag["externalDocs"] = {
                    "description": "ObserveLens Knowledge Base OpenAPI",
                    "url": "../observelens-knowledge-base/openapi.yaml",
                }
                break

    paths = schema.setdefault("paths", {})
    if isinstance(paths, dict):
        paths["/api/v1/knowledge/{path}"] = {
            "summary": "Knowledge Base reverse proxy",
            "description": (
                "Catch-all reverse proxy for observelens-knowledge-base. "
                "observelens-service only performs authentication, request context "
                "validation, and reverse proxy forwarding for /api/v1/knowledge/**. "
                "Concrete Knowledge API contracts are maintained by "
                "openapi/observelens-knowledge-base/openapi.yaml."
            ),
            "x-observelens-proxy": True,
            "x-observelens-upstream-service": "observelens-knowledge-base",
            "x-observelens-upstream-openapi": "../observelens-knowledge-base/openapi.yaml",
            "x-observelens-supported-methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS",
                "HEAD",
            ],
            "parameters": [
                {
                    "name": "X-Tenant-Id",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "integer", "format": "int64"},
                },
                {
                    "name": "X-User-Id",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "integer", "format": "int64"},
                },
                {
                    "name": "X-Request-Id",
                    "in": "header",
                    "required": False,
                    "schema": {"type": "string"},
                },
                {
                    "name": "path",
                    "in": "path",
                    "required": True,
                    "description": "Knowledge Base API path suffix to proxy.",
                    "schema": {"type": "string"},
                },
            ],
            "get": {
                "tags": ["Knowledge"],
                "summary": "Proxy Knowledge Base requests",
                "description": (
                    "Documentation placeholder for the catch-all Knowledge proxy. "
                    "The runtime gateway accepts GET, POST, PUT, PATCH, DELETE, "
                    "OPTIONS and HEAD on this path. Concrete Knowledge API contracts "
                    "are maintained by openapi/observelens-knowledge-base/openapi.yaml."
                ),
                "operationId": "proxyKnowledgeRequests",
                "responses": {
                    "default": {
                        "description": (
                            "Response proxied from observelens-knowledge-base. "
                            "See upstream OpenAPI."
                        )
                    }
                },
            },
        }

    app.openapi_schema = schema
    return app.openapi_schema


app = create_app()
