"""create incident tables

Revision ID: 20260722_0002
Revises: 20260721_0001
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260722_0002"
down_revision = "20260721_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "t_incidents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("incident_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("external_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("t_conversations.id")),
        sa.Column("started_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("create_by", sa.BigInteger(), nullable=False),
        sa.Column("update_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "update_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("delete_time", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "incident_id", name="uq_incident_tenant_reference"),
    )
    op.create_index("ix_t_incidents_tenant_id", "t_incidents", ["tenant_id"])
    op.create_index("ix_t_incidents_tenant_title", "t_incidents", ["tenant_id", "title"])
    op.create_index(
        "uq_t_incidents_tenant_conversation",
        "t_incidents",
        ["tenant_id", "conversation_id"],
        unique=True,
        postgresql_where=sa.text("conversation_id IS NOT NULL"),
    )
    op.create_table(
        "t_incident_integrations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("token_hint", sa.String(16), nullable=False),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "update_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("delete_time", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_incident_integration_tenant_name"),
    )
    op.create_index(
        "ix_t_incident_integrations_tenant_id", "t_incident_integrations", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_table("t_incident_integrations")
    op.drop_table("t_incidents")
