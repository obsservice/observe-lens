from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_auth.core.config import get_settings
from observelens_auth.core.security import hash_password
from observelens_auth.db.models import Role, Tenant, TenantMember, User

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ["*"],
    "editor": [
        "trace:read",
        "metric:read",
        "log:read",
        "topology:read",
        "incident:read",
        "incident:create",
        "incident:update",
        "knowledge_base:read",
        "knowledge_base:create",
        "knowledge_base:update",
    ],
    "viewer": [
        "trace:read",
        "metric:read",
        "log:read",
        "topology:read",
        "incident:read",
        "knowledge_base:read",
        "integration:read",
    ],
}


async def bootstrap_defaults(session: AsyncSession) -> None:
    settings = get_settings()
    roles: dict[str, Role] = {}
    for name, permissions in ROLE_PERMISSIONS.items():
        role = await session.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, display_name=name.capitalize(), permissions_json=permissions)
            session.add(role)
        roles[name] = role

    await session.flush()
    tenant = await session.scalar(
        select(Tenant).where(Tenant.name == settings.bootstrap_tenant_name)
    )
    if tenant is None:
        tenant = Tenant(
            name=settings.bootstrap_tenant_name,
            display_name=settings.bootstrap_tenant_display_name,
        )
        session.add(tenant)
        await session.flush()

    user = await session.scalar(select(User).where(User.name == settings.bootstrap_admin_username))
    if user is None:
        user = User(
            name=settings.bootstrap_admin_username,
            password_hash=hash_password(settings.bootstrap_admin_password.get_secret_value()),
            display_name="Admin",
            email=settings.bootstrap_admin_email,
        )
        session.add(user)
        await session.flush()

    member = await session.scalar(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant.id, TenantMember.user_id == user.id
        )
    )
    if member is None:
        session.add(TenantMember(tenant_id=tenant.id, user_id=user.id, role_id=roles["admin"].id))
    await session.commit()
