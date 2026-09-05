from typing import Literal

from pydantic import BaseModel, Field

IntentType = Literal["cmd", "rca", "qa"]
IntentSource = Literal["command", "rule", "llm", "fallback"]
ShortCommand = Literal["mock", "get_info", "get_metric", "analysis_incident"]
LLMIntentType = IntentType


class IntentMatch(BaseModel):
    """Intent-recognition result used to select an Agent subgraph."""

    intent_type: IntentType
    source: IntentSource
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=512)
    short_cmd: ShortCommand | None = None
    entity: str | None = None


class LLMIntentResponse(BaseModel):
    intent_type: LLMIntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=512)
    short_cmd: ShortCommand | None = None
    entity: str | None = None
