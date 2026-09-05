from fastapi import APIRouter

from observelens_agent.services.runs.router import router as runs_router
from observelens_agent.services.system.router import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(runs_router)
api_router.include_router(system_router)
