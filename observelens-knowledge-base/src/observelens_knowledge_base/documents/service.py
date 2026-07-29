from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from fastapi import UploadFile

from observelens_knowledge_base.common.context import RequestContext
from observelens_knowledge_base.common.enums import (
    DocumentSourceType,
    DocumentStatus,
    DocumentType,
    IndexTaskStatus,
    IndexTaskType,
)
from observelens_knowledge_base.common.exceptions import (
    ResourceNotFoundError,
    UnsupportedDocumentTypeError,
)
from observelens_knowledge_base.config import Settings
from observelens_knowledge_base.database.models import (
    DocumentChunkModel,
    DocumentModel,
    DocumentVersionModel,
    IndexTaskModel,
    KnowledgeBaseModel,
)
from observelens_knowledge_base.documents.indexing import SimpleDocumentChunker
from observelens_knowledge_base.documents.repository import DocumentRepository
from observelens_knowledge_base.documents.schemas import (
    ChunkConfig,
    CreateDocumentVersionResponse,
    DocumentPage,
    DocumentResponse,
    DocumentVersionResponse,
    IndexTaskResponse,
    UpdateDocumentRequest,
    UploadDocumentResponse,
)
from observelens_knowledge_base.documents.storage import DocumentStorage, StoredFile
from observelens_knowledge_base.knowledge_bases.repository import KnowledgeBaseRepository

SUPPORTED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/html",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        knowledge_base_repository: KnowledgeBaseRepository,
        storage: DocumentStorage,
        chunker: SimpleDocumentChunker,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.knowledge_base_repository = knowledge_base_repository
        self.storage = storage
        self.chunker = chunker
        self.settings = settings

    async def list_documents(
        self,
        ctx: RequestContext,
        knowledge_base_id: UUID,
        page: int,
        page_size: int,
        keyword: str | None,
        document_type: DocumentType | None,
        status: DocumentStatus | None,
        tag: str | None,
    ) -> DocumentPage:
        await self._ensure_knowledge_base(ctx, knowledge_base_id)
        items, total = await self.repository.list_documents(
            ctx.tenant_id, knowledge_base_id, page, page_size, keyword, document_type, status, tag
        )
        return DocumentPage(
            items=[DocumentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def upload(
        self,
        ctx: RequestContext,
        knowledge_base_id: UUID,
        file: UploadFile,
        name: str,
        document_type: DocumentType,
        tags: list[str],
        metadata: dict[str, Any],
    ) -> UploadDocumentResponse:
        kb = await self._ensure_knowledge_base(ctx, knowledge_base_id)
        stored_file = await self.storage.save_upload(ctx.tenant_id, file)
        self._ensure_supported_mime_type(stored_file.mime_type)
        document = DocumentModel(
            tenant_id=ctx.tenant_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            document_type=document_type,
            source_type=DocumentSourceType.UPLOAD,
            status=DocumentStatus.PENDING,
            tags=tags,
            meta=metadata,
            created_by=ctx.user_id,
        )
        self.repository.add(document)
        await self.repository.session.flush()
        version, task = await self._create_version_and_task(
            ctx, document, stored_file, IndexTaskType.INDEX, kb.embedding_model
        )
        await self._run_index_task(document, version, task)
        return UploadDocumentResponse(
            document=DocumentResponse.model_validate(document),
            version=DocumentVersionResponse.model_validate(version),
            index_task=IndexTaskResponse.model_validate(task),
        )

    async def upload_from_url(
        self,
        ctx: RequestContext,
        knowledge_base_id: UUID,
        url: str,
        name: str,
        document_type: DocumentType,
        tags: list[str],
        metadata: dict[str, Any],
    ) -> UploadDocumentResponse:
        kb = await self._ensure_knowledge_base(ctx, knowledge_base_id)

        # Download content from URL
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValidationDomainError(f"Failed to fetch URL: {exc}") from exc

        content_bytes = response.content
        content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
        # Derive filename from URL or name
        from urllib.parse import urlparse
        parsed = urlparse(url)
        file_name = Path(parsed.path).name or name

        # Save to storage
        stored_file = await self.storage.save_bytes(ctx.tenant_id, file_name, content_type, content_bytes)
        self._ensure_supported_mime_type(stored_file.mime_type)

        document = DocumentModel(
            tenant_id=ctx.tenant_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            document_type=document_type,
            source_type=DocumentSourceType.URL,
            status=DocumentStatus.PENDING,
            tags=tags,
            meta={**metadata, "source_url": url},
            created_by=ctx.user_id,
        )
        self.repository.add(document)
        await self.repository.session.flush()
        version, task = await self._create_version_and_task(
            ctx, document, stored_file, IndexTaskType.INDEX, kb.embedding_model
        )
        await self._run_index_task(document, version, task)
        return UploadDocumentResponse(
            document=DocumentResponse.model_validate(document),
            version=DocumentVersionResponse.model_validate(version),
            index_task=IndexTaskResponse.model_validate(task),
        )

    async def get(self, ctx: RequestContext, document_id: UUID) -> DocumentResponse:
        return DocumentResponse.model_validate(await self._get_document(ctx, document_id))

    async def update(
        self, ctx: RequestContext, document_id: UUID, request: UpdateDocumentRequest
    ) -> DocumentResponse:
        document = await self._get_document(ctx, document_id)
        if request.name is not None:
            document.name = request.name
        if request.document_type is not None:
            document.document_type = request.document_type
        if request.tags is not None:
            document.tags = request.tags
        if request.metadata is not None:
            document.meta = request.metadata
        await self.repository.session.flush()
        return DocumentResponse.model_validate(document)

    async def archive(self, ctx: RequestContext, document_id: UUID) -> None:
        document = await self._get_document(ctx, document_id)
        document.status = DocumentStatus.ARCHIVED
        document.archived_at = datetime.now(UTC)

    async def create_version(
        self, ctx: RequestContext, document_id: UUID, file: UploadFile, metadata: dict[str, Any]
    ) -> CreateDocumentVersionResponse:
        document = await self._get_document(ctx, document_id)
        kb = await self._ensure_knowledge_base(ctx, document.knowledge_base_id)
        if metadata:
            document.meta = {**document.meta, **metadata}
        stored_file = await self.storage.save_upload(ctx.tenant_id, file)
        self._ensure_supported_mime_type(stored_file.mime_type)
        version, task = await self._create_version_and_task(
            ctx, document, stored_file, IndexTaskType.INDEX, kb.embedding_model
        )
        await self._run_index_task(document, version, task)
        return CreateDocumentVersionResponse(
            version=DocumentVersionResponse.model_validate(version),
            index_task=IndexTaskResponse.model_validate(task),
        )

    async def list_versions(
        self, ctx: RequestContext, document_id: UUID
    ) -> list[DocumentVersionResponse]:
        await self._get_document(ctx, document_id)
        versions = await self.repository.list_versions(ctx.tenant_id, document_id)
        return [DocumentVersionResponse.model_validate(version) for version in versions]

    async def get_content_uri(
        self, ctx: RequestContext, document_id: UUID, version_id: UUID | None
    ) -> str:
        document = await self._get_document(ctx, document_id)
        target_version_id = version_id or document.current_version_id
        if target_version_id is None:
            raise ResourceNotFoundError("DOCUMENT_NOT_FOUND", "Document version")
        version = await self.repository.get_version(ctx.tenant_id, target_version_id)
        if version is None or version.document_id != document.id:
            raise ResourceNotFoundError("DOCUMENT_NOT_FOUND", "Document version")
        return version.storage_uri

    async def reindex(self, ctx: RequestContext, document_id: UUID) -> IndexTaskResponse:
        document = await self._get_document(ctx, document_id)
        if document.current_version_id is None:
            raise ResourceNotFoundError("DOCUMENT_NOT_FOUND", "Current document version")
        version = await self.repository.get_version(ctx.tenant_id, document.current_version_id)
        if version is None:
            raise ResourceNotFoundError("DOCUMENT_NOT_FOUND", "Current document version")
        task = IndexTaskModel(
            tenant_id=ctx.tenant_id,
            document_id=document.id,
            document_version_id=version.id,
            task_type=IndexTaskType.REINDEX,
            status=IndexTaskStatus.PENDING,
        )
        document.status = DocumentStatus.REINDEXING
        version.status = DocumentStatus.REINDEXING
        self.repository.add(task)
        await self.repository.session.flush()
        await self._run_index_task(document, version, task)
        return IndexTaskResponse.model_validate(task)

    async def _create_version_and_task(
        self,
        ctx: RequestContext,
        document: DocumentModel,
        stored_file: StoredFile,
        task_type: IndexTaskType,
        embedding_model: str,
    ) -> tuple[DocumentVersionModel, IndexTaskModel]:
        version_number = await self.repository.next_version_number(document.id)
        config = ChunkConfig()
        version = DocumentVersionModel(
            tenant_id=ctx.tenant_id,
            document_id=document.id,
            version=version_number,
            file_name=stored_file.file_name,
            mime_type=stored_file.mime_type,
            file_size=stored_file.file_size,
            content_hash=stored_file.content_hash,
            storage_uri=stored_file.storage_uri,
            parser_version=self.settings.parser_version,
            chunk_config=config.model_dump(),
            embedding_model=embedding_model,
            status=DocumentStatus.PENDING,
        )
        self.repository.add(version)
        await self.repository.session.flush()
        task = IndexTaskModel(
            tenant_id=ctx.tenant_id,
            document_id=document.id,
            document_version_id=version.id,
            task_type=task_type,
            status=IndexTaskStatus.PENDING,
        )
        self.repository.add(task)
        await self.repository.session.flush()
        return version, task

    async def _run_index_task(
        self, document: DocumentModel, version: DocumentVersionModel, task: IndexTaskModel
    ) -> None:
        task.status = IndexTaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        document.status = DocumentStatus.PROCESSING
        version.status = DocumentStatus.PROCESSING
        await self.repository.session.flush()
        try:
            content = await self.storage.read_text(version.storage_uri)
            chunks = self.chunker.split(content, ChunkConfig.model_validate(version.chunk_config))
            await self.repository.delete_chunks_for_version(version.id)
            self.repository.add_all(
                [
                    DocumentChunkModel(
                        tenant_id=document.tenant_id,
                        knowledge_base_id=document.knowledge_base_id,
                        document_id=document.id,
                        document_version_id=version.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        token_count=chunk.token_count,
                        title=chunk.title,
                        section_path=chunk.section_path,
                        meta={"document_type": document.document_type.value, "tags": document.tags},
                    )
                    for chunk in chunks
                ]
            )
            now = datetime.now(UTC)
            document.current_version_id = version.id
            document.status = DocumentStatus.READY
            version.status = DocumentStatus.READY
            version.indexed_at = now
            task.status = IndexTaskStatus.SUCCEEDED
            task.finished_at = now
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            version.status = DocumentStatus.FAILED
            version.error_message = str(exc)
            task.status = IndexTaskStatus.FAILED
            task.error_message = str(exc)
            task.finished_at = datetime.now(UTC)
        await self.repository.session.flush()

    async def _get_document(self, ctx: RequestContext, document_id: UUID) -> DocumentModel:
        document = await self.repository.get(ctx.tenant_id, document_id)
        if document is None:
            raise ResourceNotFoundError("DOCUMENT_NOT_FOUND", "Document")
        return document

    async def _ensure_knowledge_base(
        self, ctx: RequestContext, knowledge_base_id: UUID
    ) -> KnowledgeBaseModel:
        kb = await self.knowledge_base_repository.get(ctx.tenant_id, knowledge_base_id)
        if kb is None:
            raise ResourceNotFoundError("KNOWLEDGE_BASE_NOT_FOUND", "Knowledge base")
        return kb

    def _ensure_supported_mime_type(self, mime_type: str) -> None:
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise UnsupportedDocumentTypeError(mime_type)
