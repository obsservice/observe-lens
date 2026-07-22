from fastapi import APIRouter

from observelens_service.modules.conversations.router import router as conversations_router
from observelens_service.modules.incidents.router import router as incidents_router
from observelens_service.modules.system.router import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(conversations_router)
api_router.include_router(incidents_router)
api_router.include_router(system_router)
