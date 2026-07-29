from uuid import UUID

from sqlalchemy import delete, select

from observelens_knowledge_base.common.context import RequestContext
from observelens_knowledge_base.common.enums import KnowledgeBaseStatus
from observelens_knowledge_base.common.exceptions import ConflictError, ResourceNotFoundError
from observelens_knowledge_base.config import Settings
from observelens_knowledge_base.database.models import (
    DocumentChunkModel,
    DocumentModel,
    DocumentVersionModel,
    IndexTaskModel,
    KnowledgeBaseModel,
)
from observelens_knowledge_base.knowledge_bases.repository import KnowledgeBaseRepository
from observelens_knowledge_base.knowledge_bases.schemas import (
    CreateKnowledgeBaseRequest,
    KnowledgeBasePage,
    KnowledgeBaseResponse,
    UpdateKnowledgeBaseRequest,
)


class KnowledgeBaseService:
    def __init__(self, repository: KnowledgeBaseRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def list(
        self,
        ctx: RequestContext,
        page: int,
        page_size: int,
        keyword: str | None,
        status: KnowledgeBaseStatus | None,
    ) -> KnowledgeBasePage:
        items, total = await self.repository.list(ctx.tenant_id, page, page_size, keyword, status)
        return KnowledgeBasePage(
            items=[KnowledgeBaseResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create(
        self, ctx: RequestContext, request: CreateKnowledgeBaseRequest
    ) -> KnowledgeBaseResponse:
        existing = await self.repository.get_by_name(ctx.tenant_id, request.name)
        if existing:
            raise ConflictError("VALIDATION_FAILED", "Knowledge base name already exists")
        model = KnowledgeBaseModel(
            tenant_id=ctx.tenant_id,
            name=request.name,
            description=request.description,
            embedding_model=request.embedding_model or self.settings.embedding_model,
            created_by=ctx.user_id,
        )
        self.repository.add(model)
        await self.repository.session.flush()
        return KnowledgeBaseResponse.model_validate(model)

    async def get(self, ctx: RequestContext, knowledge_base_id: UUID) -> KnowledgeBaseResponse:
        model = await self._get_model(ctx, knowledge_base_id)
        return KnowledgeBaseResponse.model_validate(model)

    async def update(
        self, ctx: RequestContext, knowledge_base_id: UUID, request: UpdateKnowledgeBaseRequest
    ) -> KnowledgeBaseResponse:
        model = await self._get_model(ctx, knowledge_base_id)
        if request.name is not None:
            model.name = request.name
        if request.description is not None:
            model.description = request.description
        if request.status is not None:
            model.status = request.status
        if request.embedding_model is not None:
            model.embedding_model = request.embedding_model
        await self.repository.session.flush()
        return KnowledgeBaseResponse.model_validate(model)

    async def delete(self, ctx: RequestContext, knowledge_base_id: UUID) -> None:
        model = await self._get_model(ctx, knowledge_base_id)
        session = self.repository.session

        # Collect document IDs for this knowledge base
        doc_ids = list(
            (
                await session.scalars(
                    select(DocumentModel.id).where(
                        DocumentModel.knowledge_base_id == knowledge_base_id
                    )
                )
            ).all()
        )

        if doc_ids:
            # Delete chunks for all document versions belonging to these documents
            version_ids = list(
                (
                    await session.scalars(
                        select(DocumentVersionModel.id).where(
                            DocumentVersionModel.document_id.in_(doc_ids)
                        )
                    )
                ).all()
            )
            if version_ids:
                await session.execute(
                    delete(DocumentChunkModel).where(
                        DocumentChunkModel.document_version_id.in_(version_ids)
                    )
                )
            # Delete index tasks
            await session.execute(
                delete(IndexTaskModel).where(IndexTaskModel.document_id.in_(doc_ids))
            )
            # Delete document versions
            await session.execute(
                delete(DocumentVersionModel).where(
                    DocumentVersionModel.document_id.in_(doc_ids)
                )
            )
            # Delete chunks referenced by knowledge_base_id (not via version)
            await session.execute(
                delete(DocumentChunkModel).where(
                    DocumentChunkModel.knowledge_base_id == knowledge_base_id
                )
            )
            # Delete documents
            await session.execute(
                delete(DocumentModel).where(
                    DocumentModel.knowledge_base_id == knowledge_base_id
                )
            )

        await session.delete(model)

    async def _get_model(self, ctx: RequestContext, knowledge_base_id: UUID) -> KnowledgeBaseModel:
        model = await self.repository.get(ctx.tenant_id, knowledge_base_id)
        if model is None:
            raise ResourceNotFoundError("KNOWLEDGE_BASE_NOT_FOUND", "Knowledge base")
        return model
