from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observelens_knowledge_base.common.enums import (
    DocumentSourceType,
    DocumentStatus,
    DocumentType,
    IndexTaskStatus,
    IndexTaskType,
)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    tenant_id: int
    knowledge_base_id: UUID
    name: str
    document_type: DocumentType
    source_type: DocumentSourceType
    current_version_id: UUID | None
    status: DocumentStatus
    tags: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="meta")
    created_by: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class DocumentPage(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ChunkConfig(BaseModel):
    target_tokens: int = 600
    max_tokens: int = 900
    overlap_tokens: int = 100
    preserve_code_block: bool = True
    preserve_table: bool = True


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: int
    document_id: UUID
    version: int
    file_name: str
    mime_type: str
    file_size: int
    content_hash: str
    storage_uri: str
    parser_version: str
    chunk_config: dict[str, Any]
    embedding_model: str
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    indexed_at: datetime | None


class IndexTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: int
    document_id: UUID
    document_version_id: UUID
    task_type: IndexTaskType
    status: IndexTaskStatus
    retry_count: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class UploadDocumentResponse(BaseModel):
    document: DocumentResponse
    version: DocumentVersionResponse
    index_task: IndexTaskResponse


class UploadFromUrlRequest(BaseModel):
    url: str = Field(min_length=1)
    name: str = Field(min_length=1)
    document_type: DocumentType
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateDocumentVersionResponse(BaseModel):
    version: DocumentVersionResponse
    index_task: IndexTaskResponse


class UpdateDocumentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    document_type: DocumentType | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
