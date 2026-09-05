from pydantic import BaseModel


class RunStreamRequest(BaseModel):
    conversation_id: str
    run_id: str
    content: str
