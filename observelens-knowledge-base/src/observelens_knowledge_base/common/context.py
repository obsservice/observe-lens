from dataclasses import dataclass
from typing import Annotated

from fastapi import Header


@dataclass(frozen=True)
class RequestContext:
    tenant_id: int
    user_id: int
    request_id: str | None = None


async def get_request_context(
    tenant_id: Annotated[int, Header(alias="X-Tenant-Id")],
    user_id: Annotated[int, Header(alias="X-User-Id")],
    request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> RequestContext:
    return RequestContext(tenant_id=tenant_id, user_id=user_id, request_id=request_id)
