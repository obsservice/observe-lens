from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=256)


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    status: str | None = Field(default=None, pattern="^(ACTIVE|ARCHIVED|CLOSED)$")


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class ConversationPage(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ConversationCommandResponse(BaseModel):
    name: str = Field(pattern=r"^/[a-z0-9_-]+$")
    description: str
    prompt: str


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    run_id: int | None
    role: str = Field(validation_alias="sender_role")
    content: str
    metadata: dict[str, Any] | None = Field(
        default=None, validation_alias="message_metadata", serialization_alias="metadata"
    )
    created_at: datetime = Field(validation_alias="create_time")


class MessagePage(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int
