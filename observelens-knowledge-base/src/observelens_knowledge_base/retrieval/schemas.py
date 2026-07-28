from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observelens_knowledge_base.common.enums import DocumentType, RetrievalFeedbackType
from observelens_knowledge_base.common.schemas import EntityRef


class RetrievalFilters(BaseModel):
    document_types: list[DocumentType] | None = None
    tags: list[str] | None = None
    entities: list[EntityRef] | None = None
    document_ids: list[UUID] | None = None


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    knowledge_base_ids: list[UUID] | None = None
    filters: RetrievalFilters | None = None
    top_k: int = Field(default=6, ge=1, le=50)
    rerank: bool = True
    include_trace: bool = True


class Citation(BaseModel):
    document_id: UUID
    document_name: str
    document_version: int
    section: str | None = None
    page_number: int | None = None
    source_url: str
    snippet: str | None = None


class RetrievalResultMetadata(BaseModel):
    knowledge_base_id: UUID
    document_type: DocumentType | None = None
    tags: list[str] = Field(default_factory=list)
    entities: list[EntityRef] = Field(default_factory=list)
    section_path: list[str] = Field(default_factory=list)
    chunk_index: int


class RetrievalResult(BaseModel):
    chunk_id: UUID
    score: float
    content: str
    citation: Citation
    metadata: RetrievalResultMetadata


class RetrievalTrace(BaseModel):
    retrieval_id: UUID
    rewritten_query: str | None = None
    vector_candidates: int
    keyword_candidates: int
    reranked_candidates: int
    latency_ms: int


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalResult]
    trace: RetrievalTrace | None = None


class RetrievalFeedbackRequest(BaseModel):
    retrieval_log_id: UUID
    chunk_id: UUID
    rating: int = Field(ge=1, le=5)
    feedback_type: RetrievalFeedbackType
    comment: str | None = Field(default=None, max_length=2000)


class RetrievalFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: int
    retrieval_log_id: UUID
    chunk_id: UUID
    rating: int
    feedback_type: RetrievalFeedbackType
    comment: str | None
    created_by: int
    created_at: datetime


class InternalContextRetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    knowledge_base_ids: list[UUID] | None = None
    entity_type: str | None = None
    entity_name: str | None = None
    document_types: list[DocumentType] | None = None
    tags: list[str] | None = None
    top_k: int = Field(default=6, ge=1, le=20)
    conversation_id: UUID | None = None
    run_id: UUID | None = None
    roles: list[str] = Field(default_factory=list)


class KnowledgeContext(BaseModel):
    context_id: UUID
    content: str
    score: float
    citation: Citation
    document_type: DocumentType | None
    tags: list[str]


class InternalContextRetrieveResponse(BaseModel):
    retrieval_id: UUID
    query: str
    contexts: list[KnowledgeContext]
    latency_ms: int


class RetrievalLogData(BaseModel):
    query: str
    rewritten_query: str | None
    filters: dict[str, Any]
    result_chunk_ids: list[str]
    latency_ms: int
    trace_id: str | None
