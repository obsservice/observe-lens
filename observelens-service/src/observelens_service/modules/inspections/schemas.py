from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InspectionStatus = Literal["ENABLED", "DISABLED", "RUNNING", "SUCCESS", "FAILED"]


class InspectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    scope: str = Field(min_length=1, max_length=128)
    schedule: str = Field(min_length=1, max_length=128)
    input_template: str = "Run a health inspection for {{scope}}."
    enabled: bool = True


class InspectionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    scope: str | None = Field(default=None, min_length=1, max_length=128)
    schedule: str | None = Field(default=None, min_length=1, max_length=128)
    input_template: str | None = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    scope: str
    schedule: str
    status: InspectionStatus
    last_run_at: datetime | None = None
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class InspectionPage(BaseModel):
    items: list[InspectionResponse]
    total: int
    page: int
    page_size: int


class InspectionExecutionResponse(BaseModel):
    run_id: int
    status: Literal["PENDING"]
