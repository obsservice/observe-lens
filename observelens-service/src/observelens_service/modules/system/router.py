from fastapi import APIRouter

from observelens_service.config.settings import get_settings

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info")
async def get_system_info() -> dict[str, str]:
    settings = get_settings()
    return {"name": "ObserveLens", "environment": settings.environment, "version": "0.1.0"}


@router.get("/version")
async def get_system_version() -> dict[str, str]:
    return {"version": "0.1.0"}


@router.get("/health")
async def get_system_health() -> dict[str, object]:
    return {"status": "healthy", "checks": {"service": "healthy"}}
