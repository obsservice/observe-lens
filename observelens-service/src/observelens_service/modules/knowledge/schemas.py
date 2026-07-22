from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeFileResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    file_name: str
    file_type: str
    size_bytes: int = Field(ge=0)
    index_status: str
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeFilePage(BaseModel):
    items: list[KnowledgeFileResponse]
    total: int
    page: int
    page_size: int


class KnowledgeFileStatusResponse(BaseModel):
    file_id: str
    index_status: str
    failure_reason: str | None = None
