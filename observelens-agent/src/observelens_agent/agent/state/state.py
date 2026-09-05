from typing import Any

from pydantic import BaseModel, Field

from observelens_agent.agent.intents.schemas import IntentSource, IntentType, ShortCommand
from observelens_agent.agent.state.default_config import DefaultConfig
from observelens_agent.config.settings import get_settings


def _default_config() -> DefaultConfig:
    return DefaultConfig.from_settings(get_settings())


class AgentState(BaseModel):
    msg: str
    conversation_id: str = ""
    run_id: str = ""
    default_config: DefaultConfig = Field(default_factory=_default_config)
    incident: dict[str, Any] = Field(default_factory=dict)
    rag_contexts: list[dict[str, Any]] = Field(default_factory=list)
    entity_details: dict[str, Any] | None = None
    metric_results: list[dict[str, Any]] = Field(default_factory=list)
    log_results: dict[str, Any] | None = None
    trace_result: dict[str, Any] | None = None
    event_results: dict[str, Any] | None = None
    incident_report: dict[str, Any] | None = None
    run_failure_message: str | None = None
    intent_type: IntentType = "qa"
    short_cmd: ShortCommand | None = None
    entity: str | None = None
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    intent_reason: str = ""
    intent_source: IntentSource = "fallback"

    @classmethod
    def new(cls, msg: str, incident: dict[str, Any] | None = None) -> "AgentState":
        return cls(msg=msg, incident=incident or {})
