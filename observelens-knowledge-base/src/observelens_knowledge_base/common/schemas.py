from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int


class EntityRef(BaseModel):
    type: str
    name: str


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    timestamp: datetime


class ResourceTimestamps(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
