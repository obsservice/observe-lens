from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.modules.conversations.models import (
    ConversationModel,
    MessageModel,
    RunModel,
)


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, tenant_id: int, page: int, page_size: int
    ) -> tuple[list[ConversationModel], int]:
        filters = (
            ConversationModel.tenant_id == tenant_id,
            ConversationModel.delete_time.is_(None),
        )
        query: Select[tuple[ConversationModel]] = (
            select(ConversationModel).where(*filters).order_by(ConversationModel.update_time.desc())
        )
        rows = (
            await self._session.scalars(query.offset((page - 1) * page_size).limit(page_size))
        ).all()
        total = await self._session.scalar(
            select(func.count()).select_from(ConversationModel).where(*filters)
        )
        return list(rows), total or 0

    async def get(self, tenant_id: int, conversation_id: int) -> ConversationModel | None:
        result = await self._session.scalar(
            select(ConversationModel).where(
                ConversationModel.id == conversation_id,
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.delete_time.is_(None),
            )
        )
        return result

    async def next_message_sequence(self, tenant_id: int, conversation_id: int) -> int:
        sequence = await self._session.scalar(
            select(func.coalesce(func.max(MessageModel.sequence_id), 0)).where(
                MessageModel.tenant_id == tenant_id, MessageModel.conversation_id == conversation_id
            )
        )
        return int(sequence or 0) + 1

    def add(self, model: ConversationModel | MessageModel | RunModel) -> None:
        self._session.add(model)
