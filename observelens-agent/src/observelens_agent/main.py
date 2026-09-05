import warnings
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

# Suppress LangChain deprecation warning triggered during langgraph import.
# warn_deprecated() emits with category=LangChainDeprecationWarning even when pending=True,
# so we filter both.
warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change in a future version.",
    category=Warning,
)

from observelens_agent.agent.graph import build_agent_graph  # noqa: E402
from observelens_agent.services.api import api_router  # noqa: E402
from observelens_agent.clients.catalog import CatalogClient  # noqa: E402
from observelens_agent.clients.knowledge import KnowledgeClient  # noqa: E402
from observelens_agent.clients.mcp_gateway import MCPGatewayClient  # noqa: E402
from observelens_agent.common.exceptions import DomainError, domain_error_handler  # noqa: E402
from observelens_agent.config.settings import get_settings  # noqa: E402

logger = structlog.get_logger(__name__)


def build_openapi_schema(app: FastAPI) -> dict[str, object]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )
    app.openapi_schema = schema
    return schema


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    knowledge_client = KnowledgeClient(
        base_url=settings.knowledge_base_url,
        timeout_seconds=settings.knowledge_base_timeout_seconds,
        tenant_id=settings.knowledge_base_tenant_id,
        user_id=settings.knowledge_base_user_id,
        top_k=settings.incident_rag_top_k,
    )
    catalog_client = CatalogClient(
        base_url=settings.catalog_base_url,
        timeout_seconds=settings.catalog_timeout_seconds,
        workspace_id=settings.catalog_workspace_id,
    )
    gateway_client = MCPGatewayClient(
        sse_url=settings.mcp_gateway_sse_url,
        timeout_seconds=settings.mcp_gateway_timeout_seconds,
    )

    app.state.agent_graph = build_agent_graph(
        knowledge_client=knowledge_client,
        catalog_client=catalog_client,
        gateway_client=gateway_client,
    ).compile()
    logger.info("service_started", environment=settings.environment)

    yield

    logger.info("service_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="ObserveLens Agent API", version="0.1.0", lifespan=lifespan)
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


app = create_app()
