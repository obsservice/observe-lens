from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from observelens_service.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class IncidentModel(Base):
    __tablename__ = "t_incidents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    incident_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_metadata: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("t_conversations.id"), nullable=True
    )
    started_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    create_by: Mapped[int] = mapped_column(BigInteger)
    update_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now()
    )
    delete_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IncidentIntegrationModel(Base):
    __tablename__ = "t_incident_integrations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16))
    token_hint: Mapped[str] = mapped_column(String(16))
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now()
    )
    delete_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
