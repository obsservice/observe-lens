from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.enums import DocumentStatus
from observelens_knowledge_base.database.models import (
    DocumentChunkModel,
    DocumentModel,
    DocumentVersionModel,
    RetrievalFeedbackModel,
    RetrievalLogModel,
)


class RetrievalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_chunks(
        self,
        tenant_id: int,
        query: str,
        knowledge_base_ids: list[UUID] | None,
        document_ids: list[UUID] | None,
        limit: int,
    ) -> list[DocumentChunkModel]:
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.tenant_id == tenant_id)
        if knowledge_base_ids:
            stmt = stmt.where(DocumentChunkModel.knowledge_base_id.in_(knowledge_base_ids))
        if document_ids:
            stmt = stmt.where(DocumentChunkModel.document_id.in_(document_ids))
        for term in _terms(query):
            stmt = stmt.where(DocumentChunkModel.content.ilike(f"%{term}%"))
        stmt = stmt.order_by(DocumentChunkModel.created_at.desc()).limit(limit)
        return list((await self.session.scalars(stmt)).all())

    async def list_ready_chunks(
        self,
        tenant_id: int,
        knowledge_base_ids: list[UUID] | None,
        document_ids: list[UUID] | None,
        limit: int,
    ) -> list[DocumentChunkModel]:
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.tenant_id == tenant_id)
        if knowledge_base_ids:
            stmt = stmt.where(DocumentChunkModel.knowledge_base_id.in_(knowledge_base_ids))
        if document_ids:
            stmt = stmt.where(DocumentChunkModel.document_id.in_(document_ids))
        stmt = stmt.order_by(DocumentChunkModel.created_at.desc()).limit(limit)
        return list((await self.session.scalars(stmt)).all())

    async def get_document(self, tenant_id: int, document_id: UUID) -> DocumentModel | None:
        return cast(
            DocumentModel | None,
            await self.session.scalar(
                select(DocumentModel).where(
                    DocumentModel.tenant_id == tenant_id,
                    DocumentModel.id == document_id,
                    DocumentModel.status != DocumentStatus.ARCHIVED,
                )
            ),
        )

    async def get_version(self, tenant_id: int, version_id: UUID) -> DocumentVersionModel | None:
        return cast(
            DocumentVersionModel | None,
            await self.session.scalar(
                select(DocumentVersionModel).where(
                    DocumentVersionModel.tenant_id == tenant_id,
                    DocumentVersionModel.id == version_id,
                )
            ),
        )

    def add_log(self, log: RetrievalLogModel) -> None:
        self.session.add(log)

    def add_feedback(self, feedback: RetrievalFeedbackModel) -> None:
        self.session.add(feedback)


def _terms(query: str) -> list[str]:
    return [term for term in query.replace("？", " ").replace("?", " ").split() if term]
