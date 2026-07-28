from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.enums import KnowledgeBaseStatus
from observelens_knowledge_base.database.models import KnowledgeBaseModel


class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        tenant_id: int,
        page: int,
        page_size: int,
        keyword: str | None,
        status: KnowledgeBaseStatus | None,
    ) -> tuple[list[KnowledgeBaseModel], int]:
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.tenant_id == tenant_id)
        )
        if keyword:
            predicate = KnowledgeBaseModel.name.ilike(f"%{keyword}%")
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)
        if status:
            stmt = stmt.where(KnowledgeBaseModel.status == status)
            count_stmt = count_stmt.where(KnowledgeBaseModel.status == status)
        stmt = stmt.order_by(KnowledgeBaseModel.created_at.desc()).offset((page - 1) * page_size)
        stmt = stmt.limit(page_size)
        items = list((await self.session.scalars(stmt)).all())
        total = int(await self.session.scalar(count_stmt) or 0)
        return items, total

    async def get(self, tenant_id: int, knowledge_base_id: UUID) -> KnowledgeBaseModel | None:
        return cast(
            KnowledgeBaseModel | None,
            await self.session.scalar(
                select(KnowledgeBaseModel).where(
                    KnowledgeBaseModel.tenant_id == tenant_id,
                    KnowledgeBaseModel.id == knowledge_base_id,
                )
            ),
        )

    async def get_by_name(self, tenant_id: int, name: str) -> KnowledgeBaseModel | None:
        return cast(
            KnowledgeBaseModel | None,
            await self.session.scalar(
                select(KnowledgeBaseModel).where(
                    KnowledgeBaseModel.tenant_id == tenant_id,
                    KnowledgeBaseModel.name == name,
                )
            ),
        )

    def add(self, model: KnowledgeBaseModel) -> None:
        self.session.add(model)
