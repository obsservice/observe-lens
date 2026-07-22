"""create settings tables

Revision ID: 20260722_0004
Revises: 20260722_0003
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260722_0004"
down_revision = "20260722_0003"
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column[object]]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "t_llm_models",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("endpoint", sa.String(1024), nullable=True),
        sa.Column("credential", sa.String(256), nullable=True),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        *audit_columns(),
        sa.UniqueConstraint("tenant_id", "name", name="uq_llm_model_tenant_name"),
    )
    op.create_index("ix_t_llm_models_tenant_id", "t_llm_models", ["tenant_id"])
    op.create_table(
        "t_notification_channels",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("channel_type", sa.String(32), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("credential", sa.String(256), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        *audit_columns(),
        sa.UniqueConstraint("tenant_id", "name", name="uq_notification_tenant_name"),
    )
    op.create_index(
        "ix_t_notification_channels_tenant_id", "t_notification_channels", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_table("t_notification_channels")
    op.drop_table("t_llm_models")
