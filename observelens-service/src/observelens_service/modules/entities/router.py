from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.clients.catalog import CatalogClient
from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.config.settings import get_settings
from observelens_service.database.session import session_scope
from observelens_service.modules.entities.schemas import (
    EntityPage,
    EntityRelationResponse,
    EntityResponse,
    OpenEntityConversationResponse,
    TopologyResponse,
)
from observelens_service.modules.entities.service import EntityService

router = APIRouter(prefix="/entities", tags=["Entity"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[EntityService]:
    settings = get_settings()
    async with session_scope(factory) as session:
        yield EntityService(
            session,
            CatalogClient(
                str(settings.catalog_base_url) if settings.catalog_base_url else None,
                settings.catalog_timeout_seconds,
            ),
        )


ServiceDependency = Annotated[EntityService, Depends(get_service)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]


@router.get("/types")
async def list_entity_types(service: ServiceDependency) -> list[dict[str, str]]:
    return await service.types()


@router.get("/search", response_model=EntityPage)
async def search_entities(
    service: ServiceDependency,
    query: str | None = None,
    entity_type: str | None = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EntityPage:
    return await service.search(query, entity_type, page, page_size)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str, service: ServiceDependency) -> EntityResponse:
    return await service.get(entity_id)


@router.get("/{entity_id}/topology", response_model=TopologyResponse)
async def get_entity_topology(
    entity_id: str, service: ServiceDependency, depth: int = Query(2, ge=1, le=5)
) -> TopologyResponse:
    return await service.topology(entity_id, depth)


@router.get("/{entity_id}/relations", response_model=list[EntityRelationResponse])
async def list_entity_relations(
    entity_id: str, service: ServiceDependency
) -> list[EntityRelationResponse]:
    return await service.relations(entity_id)


@router.post(
    "/{entity_id}/open-conversation", response_model=OpenEntityConversationResponse, status_code=201
)
async def open_entity_conversation(
    entity_id: str, context: ContextDependency, service: ServiceDependency
) -> OpenEntityConversationResponse:
    return await service.open_conversation(context, entity_id)
