from fastapi import APIRouter

from observelens_service.modules.conversations.router import router as conversations_router
from observelens_service.modules.entities.router import router as entities_router
from observelens_service.modules.incidents.router import router as incidents_router
from observelens_service.modules.inspections.router import router as inspections_router
from observelens_service.modules.knowledge.router import router as knowledge_router
from observelens_service.modules.settings.router import router as settings_router
from observelens_service.modules.system.router import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(conversations_router)
api_router.include_router(entities_router)
api_router.include_router(incidents_router)
api_router.include_router(inspections_router)
api_router.include_router(knowledge_router)
api_router.include_router(system_router)
api_router.include_router(settings_router)
