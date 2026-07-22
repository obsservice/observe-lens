from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.clients.catalog import CatalogClient
from observelens_service.common.context import RequestContext
from observelens_service.modules.conversations.models import ConversationModel
from observelens_service.modules.conversations.service import new_id
from observelens_service.modules.entities.schemas import (
    EntityPage,
    EntityRelationResponse,
    EntityResponse,
    OpenEntityConversationResponse,
    TopologyResponse,
)


class EntityService:
    def __init__(self, session: AsyncSession, catalog_client: CatalogClient) -> None:
        self._session = session
        self._catalog_client = catalog_client

    async def types(self) -> list[dict[str, str]]:
        return await self._catalog_client.types()

    async def search(
        self, query: str | None, entity_type: str | None, page: int, page_size: int
    ) -> EntityPage:
        response = await self._catalog_client.search(query, entity_type, page, page_size)
        return EntityPage.model_validate(response)

    async def get(self, entity_id: str) -> EntityResponse:
        return EntityResponse.model_validate(await self._catalog_client.get(entity_id))

    async def topology(self, entity_id: str, depth: int) -> TopologyResponse:
        return TopologyResponse.model_validate(
            await self._catalog_client.topology(entity_id, depth)
        )

    async def relations(self, entity_id: str) -> list[EntityRelationResponse]:
        return [
            EntityRelationResponse.model_validate(item)
            for item in await self._catalog_client.relations(entity_id)
        ]

    async def open_conversation(
        self, context: RequestContext, entity_id: str
    ) -> OpenEntityConversationResponse:
        entity = await self.get(entity_id)
        conversation = ConversationModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            owner_id=context.user_id,
            title=f"Entity investigation: {entity.name}",
            status="ACTIVE",
            create_time=datetime.now(UTC),
            update_time=datetime.now(UTC),
        )
        self._session.add(conversation)
        await self._session.flush()
        return OpenEntityConversationResponse(conversation_id=conversation.id)
