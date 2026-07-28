from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from observelens_knowledge_base.api import api_router
from observelens_knowledge_base.common.exceptions import DomainError, domain_error_handler
from observelens_knowledge_base.config import get_settings
from observelens_knowledge_base.database.session import build_session_factory

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    app.state.settings = settings
    app.state.session_factory = build_session_factory(settings)
    logger.info("knowledge_base_service_started", environment=settings.environment)
    yield
    logger.info("knowledge_base_service_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.add_exception_handler(DomainError, domain_error_handler)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", request_id=request.headers.get("x-request-id", ""))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": {},
                    "trace_id": request.headers.get("x-request-id", ""),
                }
            },
        )

    return app


app = create_app()
