from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from observelens_auth.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Tenant(TimestampMixin, Base):
    __tablename__ = "t_tenant"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)


class User(TimestampMixin, Base):
    __tablename__ = "t_user"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    display_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)


class Role(TimestampMixin, Base):
    __tablename__ = "t_role"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    permissions_json: Mapped[list[str]] = mapped_column(JSON, default=list)


class TenantMember(TimestampMixin, Base):
    __tablename__ = "t_tenant_member"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_t_tenant_member_tenant_user"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("t_tenant.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("t_user.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("t_role.id"))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)


class SessionToken(Base):
    __tablename__ = "t_session_token"
    __table_args__ = (Index("ix_t_session_token_user_tenant", "user_id", "tenant_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("t_user.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("t_tenant.id", ondelete="CASCADE"), index=True
    )
    access_token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ServiceAccount(TimestampMixin, Base):
    __tablename__ = "t_service_account"
    __table_args__ = (Index("ix_t_service_account_tenant", "tenant_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("t_tenant.id", ondelete="CASCADE"))
    role_id: Mapped[UUID] = mapped_column(ForeignKey("t_role.id"))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_prefix: Mapped[str] = mapped_column(String(24), index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("t_user.id"))
