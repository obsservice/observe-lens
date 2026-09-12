from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_auth.core.config import get_settings
from observelens_auth.core.security import (
    create_access_token,
    decode_access_token,
    hash_token,
    new_refresh_token,
    new_service_token,
    verify_password,
)
from observelens_auth.db.models import (
    Role,
    ServiceAccount,
    SessionToken,
    Tenant,
    TenantMember,
    User,
)


@dataclass(frozen=True)
class Principal:
    subject_id: UUID
    tenant_id: UUID
    role_id: UUID
    role: str
    permissions: list[str]
    kind: str
    session_id: UUID | None = None
    jti: str | None = None


def forbidden(detail: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def unauthorized(detail: str = "Invalid or expired authentication credentials") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def ensure_permission(principal: Principal, permission: str) -> None:
    if "*" not in principal.permissions and permission not in principal.permissions:
        raise forbidden()


async def get_active_membership(
    session: AsyncSession, *, user_id: UUID, tenant_id: UUID
) -> tuple[TenantMember, Role] | None:
    result = await session.execute(
        select(TenantMember, Role)
        .join(Role, Role.id == TenantMember.role_id)
        .where(
            TenantMember.user_id == user_id,
            TenantMember.tenant_id == tenant_id,
            TenantMember.status == "ACTIVE",
        )
    )
    return result.one_or_none()


async def list_user_tenants(session: AsyncSession, user_id: UUID) -> list[tuple[Tenant, Role]]:
    result = await session.execute(
        select(Tenant, Role)
        .join(TenantMember, TenantMember.tenant_id == Tenant.id)
        .join(Role, Role.id == TenantMember.role_id)
        .where(
            TenantMember.user_id == user_id,
            TenantMember.status == "ACTIVE",
            Tenant.status == "ACTIVE",
        )
        .order_by(Tenant.display_name)
    )
    return list(result.all())


async def authenticate_token(session: AsyncSession, token: str) -> Principal:
    if token.startswith("olsa_"):
        return await authenticate_service_account(session, token)

    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
        session_id = UUID(payload["session_id"])
        jti = str(payload["jti"])
    except (jwt.PyJWTError, KeyError, ValueError) as error:
        raise unauthorized() from error

    token_session = await session.scalar(
        select(SessionToken).where(
            SessionToken.id == session_id,
            SessionToken.user_id == user_id,
            SessionToken.tenant_id == tenant_id,
            SessionToken.access_token_jti == jti,
            SessionToken.status == "ACTIVE",
            SessionToken.revoked_at.is_(None),
        )
    )
    user = await session.get(User, user_id)
    membership = await get_active_membership(session, user_id=user_id, tenant_id=tenant_id)
    if token_session is None or user is None or user.status != "ACTIVE" or membership is None:
        raise unauthorized()

    member, role = membership
    return Principal(
        subject_id=user_id,
        tenant_id=tenant_id,
        role_id=member.role_id,
        role=role.name,
        permissions=list(role.permissions_json),
        kind="user",
        session_id=session_id,
        jti=jti,
    )


async def authenticate_service_account(session: AsyncSession, token: str) -> Principal:
    account = await session.scalar(
        select(ServiceAccount).where(ServiceAccount.token_hash == hash_token(token))
    )
    if account is None or account.status != "ACTIVE" or account.revoked_at is not None:
        raise unauthorized()
    now = datetime.now(UTC)
    if account.expires_at is not None and account.expires_at <= now:
        raise unauthorized("Service account token has expired")
    tenant = await session.get(Tenant, account.tenant_id)
    role = await session.get(Role, account.role_id)
    if tenant is None or tenant.status != "ACTIVE" or role is None:
        raise unauthorized()
    account.last_used_at = now
    await session.commit()
    return Principal(
        subject_id=account.id,
        tenant_id=account.tenant_id,
        role_id=account.role_id,
        role=role.name,
        permissions=list(role.permissions_json),
        kind="service_account",
    )


async def issue_token_pair(
    session: AsyncSession,
    *,
    user: User,
    tenant: Tenant,
    member: TenantMember,
    role: Role,
    ip_address: str | None,
) -> tuple[str, str, datetime]:
    refresh_token = new_refresh_token()
    refresh_expiry = datetime.now(UTC) + timedelta(days=get_settings().refresh_token_expire_days)
    token_session = SessionToken(
        id=uuid4(),
        user_id=user.id,
        tenant_id=tenant.id,
        access_token_jti=str(uuid4()),
        refresh_token_hash=hash_token(refresh_token),
        ip_address=ip_address,
        expires_at=refresh_expiry,
    )
    session.add(token_session)
    await session.flush()
    access_token, access_expiry, jti = create_access_token(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=role.name,
        permissions=list(role.permissions_json),
        session_id=str(token_session.id),
    )
    token_session.access_token_jti = jti
    await session.commit()
    return access_token, refresh_token, access_expiry


async def login(
    session: AsyncSession, *, username: str, password: str, ip_address: str | None
) -> tuple[User, Tenant, Role, list[tuple[Tenant, Role]], str, str, datetime]:
    user = await session.scalar(select(User).where(User.name == username))
    if user is None or user.status != "ACTIVE" or not verify_password(password, user.password_hash):
        raise unauthorized("Incorrect username or password")
    memberships = await list_user_tenants(session, user.id)
    if not memberships:
        raise unauthorized("User is not an active member of any tenant")
    tenant, role = memberships[0]
    membership = await get_active_membership(session, user_id=user.id, tenant_id=tenant.id)
    if membership is None:
        raise unauthorized()
    member, current_role = membership
    access_token, refresh_token, access_expiry = await issue_token_pair(
        session,
        user=user,
        tenant=tenant,
        member=member,
        role=current_role,
        ip_address=ip_address,
    )
    return user, tenant, role, memberships, access_token, refresh_token, access_expiry


async def refresh(
    session: AsyncSession, *, refresh_token: str, ip_address: str | None
) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    token_session = await session.scalar(
        select(SessionToken).where(
            SessionToken.refresh_token_hash == hash_token(refresh_token),
            SessionToken.status == "ACTIVE",
            SessionToken.revoked_at.is_(None),
        )
    )
    if token_session is None or token_session.expires_at <= now:
        raise unauthorized("Invalid or expired refresh token")
    user = await session.get(User, token_session.user_id)
    tenant = await session.get(Tenant, token_session.tenant_id)
    membership = await get_active_membership(
        session, user_id=token_session.user_id, tenant_id=token_session.tenant_id
    )
    if (
        user is None
        or user.status != "ACTIVE"
        or tenant is None
        or tenant.status != "ACTIVE"
        or membership is None
    ):
        raise unauthorized()
    token_session.status = "REVOKED"
    token_session.revoked_at = now
    await session.flush()
    member, role = membership
    return await issue_token_pair(
        session, user=user, tenant=tenant, member=member, role=role, ip_address=ip_address
    )


async def revoke_session(session: AsyncSession, principal: Principal) -> None:
    if principal.session_id is None:
        return
    token_session = await session.get(SessionToken, principal.session_id)
    if token_session is not None and token_session.status == "ACTIVE":
        token_session.status = "REVOKED"
        token_session.revoked_at = datetime.now(UTC)
        await session.commit()


async def create_service_account_token() -> tuple[str, str]:
    token = new_service_token()
    return token, token[:13]
