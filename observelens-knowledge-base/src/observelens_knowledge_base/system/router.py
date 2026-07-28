from datetime import UTC, datetime

from fastapi import APIRouter

from observelens_knowledge_base import __version__
from observelens_knowledge_base.common.schemas import HealthResponse

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, timestamp=datetime.now(UTC))
