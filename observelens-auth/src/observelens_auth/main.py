import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import make_url

from observelens_auth.api.router import router
from observelens_auth.core.config import get_settings
from observelens_auth.db.session import SessionLocal
from observelens_auth.services.bootstrap import bootstrap_defaults

logger = logging.getLogger(__name__)


def database_url_for_logs() -> str:
    """Return a database URL suitable for logs without exposing its password."""
    try:
        return make_url(get_settings().database_url).render_as_string(hide_password=True)
    except Exception:
        return "<invalid AUTH_DATABASE_URL>"


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        async with SessionLocal() as session:
            await bootstrap_defaults(session)
    except Exception as error:
        logger.exception("ObserveLens Auth failed to initialize its database")
        logger.error(
            "Startup aborted: unable to initialize PostgreSQL at %s. Reason: %s. "
            "Check that PostgreSQL is running and that AUTH_DATABASE_URL uses the correct host "
            "and port (localhost:5433 for the bundled Docker database; postgres:5432 inside "
            "Docker Compose).",
            database_url_for_logs(),
            error,
        )
        raise
    yield


app = FastAPI(
    title="ObserveLens Auth API",
    version="0.1.0",
    summary="ObserveLens 多租户认证与授权服务",
    description=(
        "提供用户认证、JWT 令牌校验、租户切换、成员管理及服务账号管理能力。"
        "所有受保护资源均由 token 中的 tenant_id 进行租户隔离。"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
