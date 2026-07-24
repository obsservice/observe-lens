from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
Status = Literal["OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED", "CLOSED", "ARCHIVED"]
SUPPORTED_INTEGRATION_TYPES = [
    "Webhook",
    "AlertManager",
    "Grafana",
    "Prometheus",
    "Datadog",
    "Zabbix",
    "Nagios",
    "OpsGenie",
]
IntegrationType = Literal[
    "Webhook",
    "AlertManager",
    "Grafana",
    "Prometheus",
    "Datadog",
    "Zabbix",
    "Nagios",
    "OpsGenie",
]
IntegrationStatus = Literal["ENABLED", "DISABLED"]


class IncidentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    severity: Severity = "MEDIUM"
    source: str | None = Field(default="MANUAL", max_length=64)
    started_at: datetime | None = None
    external_metadata: dict[str, str] = Field(default_factory=dict)


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
    status: IntegrationStatus = "ENABLED"


class IntegrationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    type: IntegrationType | None = None
    status: IntegrationStatus | None = None


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
