from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from observelens_service.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ModelConfigModel(Base):
    __tablename__ = "t_llm_models"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    endpoint: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    credential: Mapped[str | None] = mapped_column(String(256), nullable=True)
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    create_by: Mapped[int] = mapped_column(BigInteger)
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now()
    )
    delete_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationModel(Base):
    __tablename__ = "t_notification_channels"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(128))
    channel_type: Mapped[str] = mapped_column(String(32))
    config: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    credential: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    create_by: Mapped[int] = mapped_column(BigInteger)
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now()
    )
    delete_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
