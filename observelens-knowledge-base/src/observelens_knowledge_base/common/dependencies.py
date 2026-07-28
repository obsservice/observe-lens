from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.database.session import session_scope


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with session_scope(request.app.state.session_factory) as session:
        yield session
