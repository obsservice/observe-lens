from __future__ import annotations

from typing import cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.enums import DocumentStatus, DocumentType
from observelens_knowledge_base.database.models import (
    DocumentChunkModel,
    DocumentModel,
    DocumentVersionModel,
    IndexTaskModel,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_documents(
        self,
        tenant_id: int,
        knowledge_base_id: UUID,
        page: int,
        page_size: int,
        keyword: str | None,
        document_type: DocumentType | None,
        status: DocumentStatus | None,
        tag: str | None,
    ) -> tuple[list[DocumentModel], int]:
        stmt = select(DocumentModel).where(
            DocumentModel.tenant_id == tenant_id,
            DocumentModel.knowledge_base_id == knowledge_base_id,
        )
        count_stmt = (
            select(func.count())
            .select_from(DocumentModel)
            .where(
                DocumentModel.tenant_id == tenant_id,
                DocumentModel.knowledge_base_id == knowledge_base_id,
            )
        )
        if keyword:
            predicate = DocumentModel.name.ilike(f"%{keyword}%")
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)
        if document_type:
            stmt = stmt.where(DocumentModel.document_type == document_type)
            count_stmt = count_stmt.where(DocumentModel.document_type == document_type)
        if status:
            stmt = stmt.where(DocumentModel.status == status)
            count_stmt = count_stmt.where(DocumentModel.status == status)
        if tag:
            stmt = stmt.where(DocumentModel.tags.contains([tag]))
            count_stmt = count_stmt.where(DocumentModel.tags.contains([tag]))
        stmt = stmt.order_by(DocumentModel.created_at.desc()).offset((page - 1) * page_size)
        stmt = stmt.limit(page_size)
        return list((await self.session.scalars(stmt)).all()), int(
            await self.session.scalar(count_stmt) or 0
        )

    async def get(self, tenant_id: int, document_id: UUID) -> DocumentModel | None:
        return cast(
            DocumentModel | None,
            await self.session.scalar(
                select(DocumentModel).where(
                    DocumentModel.tenant_id == tenant_id,
                    DocumentModel.id == document_id,
                )
            ),
        )

    async def next_version_number(self, document_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(DocumentVersionModel.version)).where(
                DocumentVersionModel.document_id == document_id
            )
        )
        return int(current or 0) + 1

    async def list_versions(self, tenant_id: int, document_id: UUID) -> list[DocumentVersionModel]:
        return list(
            (
                await self.session.scalars(
                    select(DocumentVersionModel)
                    .where(
                        DocumentVersionModel.tenant_id == tenant_id,
                        DocumentVersionModel.document_id == document_id,
                    )
                    .order_by(DocumentVersionModel.version.desc())
                )
            ).all()
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

    async def delete_chunks_for_version(self, document_version_id: UUID) -> None:
        await self.session.execute(
            delete(DocumentChunkModel).where(
                DocumentChunkModel.document_version_id == document_version_id
            )
        )

    def add(self, model: object) -> None:
        self.session.add(model)

    def add_all(self, models: list[object]) -> None:
        self.session.add_all(models)

    async def get_task(self, tenant_id: int, task_id: UUID) -> IndexTaskModel | None:
        return cast(
            IndexTaskModel | None,
            await self.session.scalar(
                select(IndexTaskModel).where(
                    IndexTaskModel.tenant_id == tenant_id,
                    IndexTaskModel.id == task_id,
                )
            ),
        )
