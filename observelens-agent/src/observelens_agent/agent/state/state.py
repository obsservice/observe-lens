from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    msg: str
    incident: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def new(cls, msg: str, incident: dict[str, Any] | None = None) -> "AgentState":
        return cls(msg=msg, incident=incident or {})
