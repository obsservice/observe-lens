from datetime import UTC, datetime
from typing import Any
from uuid import UUID as PyUUID
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from observelens_knowledge_base.common.enums import (
    DocumentSourceType,
    DocumentStatus,
    DocumentType,
    IndexTaskStatus,
    IndexTaskType,
    KnowledgeBaseStatus,
    RetrievalFeedbackType,
)
from observelens_knowledge_base.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class KnowledgeBaseModel(Base):
    __tablename__ = "t_knowledge_bases"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_knowledge_bases_tenant_name"),)

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[KnowledgeBaseStatus] = mapped_column(
        Enum(KnowledgeBaseStatus, native_enum=False), default=KnowledgeBaseStatus.ACTIVE
    )
    embedding_model: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    documents: Mapped[list["DocumentModel"]] = relationship(back_populates="knowledge_base")


class DocumentModel(Base):
    __tablename__ = "t_documents"

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    knowledge_base_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("t_knowledge_bases.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False))
    source_type: Mapped[DocumentSourceType] = mapped_column(
        Enum(DocumentSourceType, native_enum=False), default=DocumentSourceType.UPLOAD
    )
    current_version_id: Mapped[PyUUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.UPLOADED
    )
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    knowledge_base: Mapped[KnowledgeBaseModel] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersionModel"]] = relationship(back_populates="document")


class DocumentVersionModel(Base):
    __tablename__ = "t_document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_document_versions_number"),
    )

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    document_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("t_documents.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(BigInteger)
    content_hash: Mapped[str] = mapped_column(String(128))
    storage_uri: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(255))
    chunk_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    embedding_model: Mapped[str] = mapped_column(String(255))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[DocumentModel] = relationship(back_populates="versions")


class DocumentChunkModel(Base):
    __tablename__ = "t_document_chunks"

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    knowledge_base_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    document_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    document_version_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(255))
    section_path: Mapped[list[str]] = mapped_column(JSONB, default=list)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class IndexTaskModel(Base):
    __tablename__ = "t_index_tasks"

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    document_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    document_version_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    task_type: Mapped[IndexTaskType] = mapped_column(Enum(IndexTaskType, native_enum=False))
    status: Mapped[IndexTaskStatus] = mapped_column(
        Enum(IndexTaskStatus, native_enum=False), default=IndexTaskStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RetrievalLogModel(Base):
    __tablename__ = "t_retrieval_logs"

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    query: Mapped[str] = mapped_column(Text)
    rewritten_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    result_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RetrievalFeedbackModel(Base):
    __tablename__ = "t_retrieval_feedback"

    id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    retrieval_log_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    chunk_id: Mapped[PyUUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    feedback_type: Mapped[RetrievalFeedbackType] = mapped_column(
        Enum(RetrievalFeedbackType, native_enum=False)
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
