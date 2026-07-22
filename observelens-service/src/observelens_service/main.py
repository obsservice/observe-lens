from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
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
    app = FastAPI(title="ObserveLens API", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router)
    app.add_exception_handler(DomainError, domain_error_handler)

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
