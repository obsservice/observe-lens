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
from observelens_agent.api import api_router  # noqa: E402
from observelens_agent.common.exceptions import DomainError, domain_error_handler  # noqa: E402
from observelens_agent.config.settings import get_settings  # noqa: E402

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.agent_graph = build_agent_graph().compile()
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


app = create_app()
