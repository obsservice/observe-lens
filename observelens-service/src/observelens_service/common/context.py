from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestContext:
    tenant_id: int
    user_id: int
    request_id: str
