from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    msg: str
    conversation_id: str = ""
    run_id: str = ""
    incident: dict[str, Any] = Field(default_factory=dict)
    intent: Literal["mock", "agent"] = "agent"

    @classmethod
    def new(cls, msg: str, incident: dict[str, Any] | None = None) -> "AgentState":
        return cls(msg=msg, incident=incident or {})
