from typing import Any, Literal

from pydantic import BaseModel, Field

IntentName = Literal["mock", "get_info", "get_metric", "analysis_incident", "general"]
IntentSource = Literal["command", "regex", "llm", "fallback"]


class AgentState(BaseModel):
    msg: str
    conversation_id: str = ""
    run_id: str = ""
    incident: dict[str, Any] = Field(default_factory=dict)
    entity_details: dict[str, Any] | None = None
    intent: IntentName = "general"
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    intent_reason: str = ""
    intent_source: IntentSource = "fallback"

    @classmethod
    def new(cls, msg: str, incident: dict[str, Any] | None = None) -> "AgentState":
        return cls(msg=msg, incident=incident or {})
