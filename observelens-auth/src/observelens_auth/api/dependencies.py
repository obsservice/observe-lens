from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_auth.api.schemas import VerifyTokenResponse
from observelens_auth.db.session import get_db
from observelens_auth.services.auth import (
    Principal,
    authenticate_token,
    ensure_permission,
    unauthorized,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized("Bearer token is required")
    return await authenticate_token(session, credentials.credentials)


def require_permission(permission: str) -> Callable[[Principal], Principal]:
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        ensure_permission(principal, permission)
        return principal

    return dependency


async def verify_optional_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> VerifyTokenResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return VerifyTokenResponse(valid=False)
    try:
        principal = await authenticate_token(session, credentials.credentials)
    except HTTPException:
        return VerifyTokenResponse(valid=False)
    expires_at = None
    if principal.kind == "user":
        from observelens_auth.core.security import decode_access_token

        expires_at = int(decode_access_token(credentials.credentials)["exp"])
    return VerifyTokenResponse(
        valid=True,
        user_id=principal.subject_id if principal.kind == "user" else None,
        tenant_id=principal.tenant_id,
        role=principal.role,
        permissions=principal.permissions,
        expires_at=expires_at,
        subject_type=principal.kind,
    )
