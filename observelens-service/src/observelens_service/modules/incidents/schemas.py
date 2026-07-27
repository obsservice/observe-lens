from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_INCIDENT_SEVERITIES = ["Critical", "Error", "Warn"]
Severity = Literal["Critical", "Error", "Warn"]
SUPPORTED_INCIDENT_STATUSES = [
    "Open",
    "Acknowledged",
    "Investigating",
    "Recovering",
    "Resolved",
    "Closed",
    "Archived",
]
Status = Literal[
    "Open",
    "Acknowledged",
    "Investigating",
    "Recovering",
    "Resolved",
    "Closed",
    "Archived",
]
SUPPORTED_INTEGRATION_TYPES = [
    "Webhook",
    "Alertmanager",
]
IntegrationType = Literal[
    "Webhook",
    "Alertmanager",
]
IntegrationStatus = Literal["Enabled", "Disabled"]

TRANSITION_RULES: dict[str, list[str]] = {
    "Open": ["Acknowledged", "Investigating"],
    "Acknowledged": ["Investigating"],
    "Investigating": ["Recovering"],
    "Recovering": ["Resolved"],
    "Resolved": ["Closed"],
    "Closed": [],
    "Archived": [],
}


class TransitionRequest(BaseModel):
    status: str
    assignee: str | None = None


class IncidentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    severity: Severity | None = None
    status: Status | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: str
    name: str = Field(validation_alias="title")
    description: str | None
    severity: str
    status: str
    source: str | None
    external_metadata: dict[str, str] = Field(default_factory=dict)
    started_at: datetime | None = Field(validation_alias="started_time")
    conversation_id: int | None
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class IncidentPage(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int


class IntegrationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: IntegrationType = "Webhook"
    status: IntegrationStatus = "Enabled"


class IntegrationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    type: IntegrationType | None = None
    status: IntegrationStatus | None = None


class WebhookIncidentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    severity: Severity = "Warn"
    source: str | None = Field(default=None, max_length=128)
    started_at: datetime | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class AlertmanagerAlert(BaseModel):
    status: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: datetime | None = None
    endsAt: datetime | None = None


class AlertmanagerWebhookRequest(BaseModel):
    receiver: str | None = None
    status: str | None = None
    source: str | None = Field(default=None, max_length=128)
    alerts: list[AlertmanagerAlert] = Field(default_factory=list)
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = None


class IncidentIntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    status: str
    webhook_url: str = ""
    token: str
    token_hint: str
    created_at: datetime = Field(validation_alias="create_time")
    updated_at: datetime = Field(validation_alias="update_time")


class OpenConversationResponse(BaseModel):
    conversation_id: int
