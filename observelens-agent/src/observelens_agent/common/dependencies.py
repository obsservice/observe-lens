from typing import Annotated

from fastapi import Header

from observelens_agent.common.context import RequestContext


async def get_request_context(
    x_tenant_id: Annotated[int, Header()],
    x_user_id: Annotated[int, Header()],
    x_request_id: Annotated[str | None, Header()] = None,
) -> RequestContext:
    return RequestContext(tenant_id=x_tenant_id, user_id=x_user_id, request_id=x_request_id or "")
