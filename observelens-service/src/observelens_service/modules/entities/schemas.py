from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EntityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    type: str
    namespace: str = ""
    status: str = "UNKNOWN"
    labels: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)
    updated_at: datetime | None = None


class EntityPage(BaseModel):
    items: list[EntityResponse]
    total: int
    page: int
    page_size: int


class EntityRelationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    source_entity_id: str
    target_entity_id: str
    type: str
    metadata: dict[str, object] = Field(default_factory=dict)


class TopologyResponse(BaseModel):
    nodes: list[EntityResponse]
    edges: list[EntityRelationResponse]


class OpenEntityConversationResponse(BaseModel):
    conversation_id: int
