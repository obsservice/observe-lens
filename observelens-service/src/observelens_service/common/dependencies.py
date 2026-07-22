from typing import Annotated

from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.common.context import RequestContext


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory  # type: ignore[no-any-return]


async def get_request_context(
    x_tenant_id: Annotated[int, Header()],
    x_user_id: Annotated[int, Header()],
    x_request_id: Annotated[str | None, Header()] = None,
) -> RequestContext:
    return RequestContext(tenant_id=x_tenant_id, user_id=x_user_id, request_id=x_request_id or "")
