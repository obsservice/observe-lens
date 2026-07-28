from fastapi import APIRouter

from observelens_knowledge_base.documents.router import router as documents_router
from observelens_knowledge_base.index_tasks.router import router as index_tasks_router
from observelens_knowledge_base.knowledge_bases.router import router as knowledge_bases_router
from observelens_knowledge_base.retrieval.router import router as retrieval_router
from observelens_knowledge_base.system.router import router as system_router

api_router = APIRouter(prefix="/api/v1/knowledge")
api_router.include_router(knowledge_bases_router)
api_router.include_router(documents_router)
api_router.include_router(retrieval_router)
api_router.include_router(index_tasks_router)
api_router.include_router(system_router)
