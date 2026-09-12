from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TenantSummary(APIModel):
    id: UUID
    name: str
    display_name: str
    role: str


class TenantDetail(APIModel):
    id: UUID
    name: str
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserResponse(APIModel):
    id: UUID
    name: str
    email: str
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    current_tenant: TenantSummary
    tenants: list[TenantSummary]


class SwitchTenantRequest(BaseModel):
    tenant_id: UUID


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshTokenResponse(AccessTokenResponse):
    refresh_token: str


class CurrentUserResponse(UserResponse):
    current_tenant: TenantSummary
    permissions: list[str]
    tenants: list[TenantSummary]


class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: UUID | None = None
    tenant_id: UUID | None = None
    role: str | None = None
    permissions: list[str] = Field(default_factory=list)
    expires_at: int | None = None
    subject_type: str | None = None


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=128)
    email: EmailStr


class CreateTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=1, max_length=128)


class RoleResponse(APIModel):
    id: UUID
    name: str
    display_name: str
    permissions_json: list[str]


class MemberResponse(APIModel):
    id: UUID
    user: UserResponse
    role: RoleResponse
    status: str
    created_at: datetime
    updated_at: datetime


class CreateMemberRequest(BaseModel):
    user_id: UUID
    role_id: UUID


class UpdateMemberRequest(BaseModel):
    role_id: UUID | None = None
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|DISABLED)$")


class CreateServiceAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    role_id: UUID
    expires_at: datetime | None = None


class UpdateServiceAccountRequest(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    role_id: UUID | None = None
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|DISABLED|REVOKED)$")
    expires_at: datetime | None = None


class ServiceAccountResponse(APIModel):
    id: UUID
    name: str
    description: str | None
    tenant_id: UUID
    role_id: UUID
    status: str
    token_prefix: str
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class CreatedServiceAccountResponse(ServiceAccountResponse):
    token: str


class PaginatedServiceAccounts(BaseModel):
    items: list[ServiceAccountResponse]
    page: int
    page_size: int
    total: int
