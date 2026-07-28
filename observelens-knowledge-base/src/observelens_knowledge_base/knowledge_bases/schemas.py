from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observelens_knowledge_base.common.enums import KnowledgeBaseStatus


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: int
    name: str
    description: str | None
    status: KnowledgeBaseStatus
    embedding_model: str
    created_by: int
    created_at: datetime
    updated_at: datetime


class KnowledgeBasePage(BaseModel):
    items: list[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int


class CreateKnowledgeBaseRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    embedding_model: str | None = None


class UpdateKnowledgeBaseRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: KnowledgeBaseStatus | None = None
    embedding_model: str | None = None
