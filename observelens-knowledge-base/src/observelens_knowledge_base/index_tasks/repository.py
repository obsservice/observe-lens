from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.database.models import IndexTaskModel


class IndexTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, tenant_id: int, task_id: UUID) -> IndexTaskModel | None:
        return cast(
            IndexTaskModel | None,
            await self.session.scalar(
                select(IndexTaskModel).where(
                    IndexTaskModel.tenant_id == tenant_id,
                    IndexTaskModel.id == task_id,
                )
            ),
        )
