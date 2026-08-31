from typing import Literal

from pydantic import BaseModel, Field

from observelens_agent.agent.state.state import IntentName, IntentSource

LLMIntentName = Literal["get_info", "get_metric", "analysis_incident", "general"]


class IntentMatch(BaseModel):
    intent: IntentName
    source: IntentSource
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=512)


class LLMIntentResponse(BaseModel):
    intent: LLMIntentName
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=512)
