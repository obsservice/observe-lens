from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_auth.api.dependencies import (
    get_current_principal,
    require_permission,
    verify_optional_token,
)
from observelens_auth.api.schemas import (
    AccessTokenResponse,
    CreatedServiceAccountResponse,
    CreateMemberRequest,
    CreateServiceAccountRequest,
    CreateTenantRequest,
    CreateUserRequest,
    CurrentUserResponse,
    LoginRequest,
    MemberResponse,
    PaginatedServiceAccounts,
    RefreshRequest,
    RefreshTokenResponse,
    RoleResponse,
    ServiceAccountResponse,
    SwitchTenantRequest,
    TenantDetail,
    TenantSummary,
    TokenResponse,
    UpdateMemberRequest,
    UpdateServiceAccountRequest,
    UserResponse,
    VerifyTokenResponse,
)
from observelens_auth.core.security import hash_password, hash_token
from observelens_auth.db.models import Role, ServiceAccount, Tenant, TenantMember, User
from observelens_auth.db.session import get_db
from observelens_auth.services.auth import (
    Principal,
    create_service_account_token,
    ensure_permission,
    get_active_membership,
    issue_token_pair,
    list_user_tenants,
    login,
    refresh,
    revoke_session,
)

router = APIRouter(prefix="/api/v1")


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client is not None else None


def tenant_summary(tenant: Tenant, role: Role) -> TenantSummary:
    return TenantSummary(
        id=tenant.id, name=tenant.name, display_name=tenant.display_name, role=role.name
    )


def member_response(member: TenantMember, user: User, role: Role) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        user=UserResponse.model_validate(user),
        role=RoleResponse.model_validate(role),
        status=member.status,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login_endpoint(
    body: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user, tenant, role, tenants, access_token, refresh_token, access_expiry = await login(
        session, username=body.username, password=body.password, ip_address=client_ip(request)
    )
    summaries = [tenant_summary(item_tenant, item_role) for item_tenant, item_role in tenants]
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int((access_expiry - datetime.now(UTC)).total_seconds()),
        current_tenant=tenant_summary(tenant, role),
        tenants=summaries,
    )


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_endpoint(
    body: RefreshRequest, request: Request, session: AsyncSession = Depends(get_db)
) -> RefreshTokenResponse:
    access_token, refresh_token, access_expiry = await refresh(
        session, refresh_token=body.refresh_token, ip_address=client_ip(request)
    )
    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int((access_expiry - datetime.now(UTC)).total_seconds()),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(
    principal: Principal = Depends(get_current_principal), session: AsyncSession = Depends(get_db)
) -> Response:
    await revoke_session(session, principal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=CurrentUserResponse)
async def me_endpoint(
    principal: Principal = Depends(get_current_principal), session: AsyncSession = Depends(get_db)
) -> CurrentUserResponse:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    user = await session.get(User, principal.subject_id)
    tenant = await session.get(Tenant, principal.tenant_id)
    if user is None or tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    tenants = await list_user_tenants(session, user.id)
    return CurrentUserResponse(
        **UserResponse.model_validate(user).model_dump(),
        current_tenant=TenantSummary(
            id=tenant.id, name=tenant.name, display_name=tenant.display_name, role=principal.role
        ),
        permissions=principal.permissions,
        tenants=[tenant_summary(item_tenant, item_role) for item_tenant, item_role in tenants],
    )


@router.post("/auth/switch-tenant", response_model=AccessTokenResponse)
async def switch_tenant_endpoint(
    body: SwitchTenantRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    user = await session.get(User, principal.subject_id)
    tenant = await session.get(Tenant, body.tenant_id)
    membership = await get_active_membership(
        session, user_id=principal.subject_id, tenant_id=body.tenant_id
    )
    if user is None or tenant is None or tenant.status != "ACTIVE" or membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not an active tenant member"
        )
    member, role = membership
    access_token, _, access_expiry = await issue_token_pair(
        session, user=user, tenant=tenant, member=member, role=role, ip_address=client_ip(request)
    )
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=int((access_expiry - datetime.now(UTC)).total_seconds()),
    )


@router.post("/auth/verify-token", response_model=VerifyTokenResponse)
async def verify_token_endpoint(
    result: VerifyTokenResponse = Depends(verify_optional_token),
) -> VerifyTokenResponse:
    return result


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    result = await session.scalars(
        select(User)
        .join(TenantMember, TenantMember.user_id == User.id)
        .where(TenantMember.tenant_id == principal.tenant_id)
        .order_by(User.name)
    )
    return [UserResponse.model_validate(user) for user in result.unique().all()]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    viewer = await session.scalar(select(Role).where(Role.name == "viewer"))
    if viewer is None:
        raise HTTPException(status_code=500, detail="Default roles are not initialized")
    user = User(
        name=body.name,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        email=str(body.email),
    )
    session.add(user)
    await session.flush()
    session.add(TenantMember(tenant_id=principal.tenant_id, user_id=user.id, role_id=viewer.id))
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from error
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/users/current", response_model=UserResponse)
async def current_user(
    principal: Principal = Depends(get_current_principal), session: AsyncSession = Depends(get_db)
) -> UserResponse:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    user = await session.get(User, principal.subject_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    _: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> list[RoleResponse]:
    roles = await session.scalars(select(Role).order_by(Role.name))
    return [RoleResponse.model_validate(role) for role in roles]


@router.get("/tenants", response_model=list[TenantDetail])
async def list_tenants(
    principal: Principal = Depends(get_current_principal), session: AsyncSession = Depends(get_db)
) -> list[TenantDetail]:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    tenants = await list_user_tenants(session, principal.subject_id)
    return [TenantDetail.model_validate(tenant) for tenant, _ in tenants]


@router.post("/tenants", response_model=TenantDetail, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: CreateTenantRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> TenantDetail:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    admin = await session.scalar(select(Role).where(Role.name == "admin"))
    if admin is None:
        raise HTTPException(status_code=500, detail="Default roles are not initialized")
    tenant = Tenant(name=body.name, display_name=body.display_name)
    session.add(tenant)
    await session.flush()
    session.add(TenantMember(tenant_id=tenant.id, user_id=principal.subject_id, role_id=admin.id))
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Tenant name already exists") from error
    await session.refresh(tenant)
    return TenantDetail.model_validate(tenant)


@router.get("/tenants/current", response_model=TenantDetail)
async def current_tenant(
    principal: Principal = Depends(get_current_principal), session: AsyncSession = Depends(get_db)
) -> TenantDetail:
    tenant = await session.get(Tenant, principal.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantDetail.model_validate(tenant)


@router.get("/tenants/current/members", response_model=list[MemberResponse])
async def list_members(
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    result = await session.execute(
        select(TenantMember, User, Role)
        .join(User, User.id == TenantMember.user_id)
        .join(Role, Role.id == TenantMember.role_id)
        .where(TenantMember.tenant_id == principal.tenant_id)
        .order_by(User.name)
    )
    return [member_response(member, user, role) for member, user, role in result.all()]


@router.post(
    "/tenants/current/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED
)
async def create_member(
    body: CreateMemberRequest,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    ensure_permission(principal, "tenant:manage")
    user = await session.get(User, body.user_id)
    role = await session.get(Role, body.role_id)
    if user is None or role is None:
        raise HTTPException(status_code=404, detail="User or role not found")
    member = TenantMember(tenant_id=principal.tenant_id, user_id=user.id, role_id=role.id)
    session.add(member)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="User is already a tenant member") from error
    await session.refresh(member)
    return member_response(member, user, role)


@router.patch("/tenants/current/members/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    body: UpdateMemberRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    result = await session.execute(
        select(TenantMember, User, Role)
        .join(User, User.id == TenantMember.user_id)
        .join(Role, Role.id == TenantMember.role_id)
        .where(TenantMember.id == member_id, TenantMember.tenant_id == principal.tenant_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    member, user, role = row
    if body.role_id is not None:
        new_role = await session.get(Role, body.role_id)
        if new_role is None:
            raise HTTPException(status_code=404, detail="Role not found")
        member.role_id = new_role.id
        role = new_role
    if body.status is not None:
        member.status = body.status
    await session.commit()
    await session.refresh(member)
    return member_response(member, user, role)


@router.delete("/tenants/current/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: UUID,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> Response:
    member = await session.scalar(
        select(TenantMember).where(
            TenantMember.id == member_id, TenantMember.tenant_id == principal.tenant_id
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.user_id == principal.subject_id:
        raise HTTPException(status_code=400, detail="Cannot remove the current user")
    await session.delete(member)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/service-accounts",
    response_model=CreatedServiceAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_account(
    body: CreateServiceAccountRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> CreatedServiceAccountResponse:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User token is required")
    role = await session.get(Role, body.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if body.expires_at is not None and body.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="expires_at must be in the future")
    token, token_prefix = await create_service_account_token()
    account = ServiceAccount(
        name=body.name,
        description=body.description,
        tenant_id=principal.tenant_id,
        role_id=body.role_id,
        token_hash=hash_token(token),
        token_prefix=token_prefix,
        expires_at=body.expires_at,
        created_by_user_id=principal.subject_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return CreatedServiceAccountResponse(
        **ServiceAccountResponse.model_validate(account).model_dump(), token=token
    )


@router.get("/service-accounts", response_model=PaginatedServiceAccounts)
async def list_service_accounts(
    page: int = 1,
    page_size: int = 20,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> PaginatedServiceAccounts:
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=422, detail="page must be >= 1 and page_size must be between 1 and 100"
        )
    base = select(ServiceAccount).where(ServiceAccount.tenant_id == principal.tenant_id)
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    accounts = await session.scalars(
        base.order_by(ServiceAccount.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return PaginatedServiceAccounts(
        items=[ServiceAccountResponse.model_validate(account) for account in accounts],
        page=page,
        page_size=page_size,
        total=total or 0,
    )


@router.patch("/service-accounts/{service_account_id}", response_model=ServiceAccountResponse)
async def update_service_account(
    service_account_id: UUID,
    body: UpdateServiceAccountRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
    session: AsyncSession = Depends(get_db),
) -> ServiceAccountResponse:
    account = await session.scalar(
        select(ServiceAccount).where(
            ServiceAccount.id == service_account_id, ServiceAccount.tenant_id == principal.tenant_id
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Service account not found")
    if body.role_id is not None:
        if await session.get(Role, body.role_id) is None:
            raise HTTPException(status_code=404, detail="Role not found")
        account.role_id = body.role_id
    if body.description is not None:
        account.description = body.description
    if body.expires_at is not None:
        if body.expires_at <= datetime.now(UTC):
            raise HTTPException(status_code=422, detail="expires_at must be in the future")
        account.expires_at = body.expires_at
    if body.status is not None:
        if account.revoked_at is not None and body.status == "ACTIVE":
            raise HTTPException(
                status_code=409, detail="Revoked service accounts cannot be reactivated"
            )
        account.status = body.status
        if body.status == "REVOKED":
            account.revoked_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(account)
    return ServiceAccountResponse.model_validate(account)
