from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ModelWrite(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider: str
    model_name: str
    endpoint: str | None = None
    credential_ref: str | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    provider: str
    model_name: str
    endpoint: str | None
    status: str
    is_default: bool
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class ModelPage(BaseModel):
    items: list[ModelResponse]
    total: int
    page: int
    page_size: int


class NotificationWrite(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    channel_type: str
    target: str
    credential_ref: str | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str = Field(validation_alias="channel_type")
    status: str
    target: str
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class NotificationPage(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class TestResult(BaseModel):
    status: str
    message: str
