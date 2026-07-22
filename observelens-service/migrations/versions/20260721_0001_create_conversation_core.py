"""create conversation core tables

Revision ID: 20260721_0001
Revises:
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "20260721_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "t_conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
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
    )
    op.create_index("ix_t_conversations_tenant_id", "t_conversations", ["tenant_id"])
    op.create_table(
        "t_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "conversation_id", sa.BigInteger(), sa.ForeignKey("t_conversations.id"), nullable=False
        ),
        sa.Column("sequence_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tenant_id", "conversation_id", "sequence_id", name="uq_message_sequence"
        ),
    )
    op.create_index("ix_t_messages_tenant_id", "t_messages", ["tenant_id"])
    op.create_index("ix_t_messages_conversation_id", "t_messages", ["conversation_id"])
    op.create_table(
        "t_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "conversation_id", sa.BigInteger(), sa.ForeignKey("t_conversations.id"), nullable=False
        ),
        sa.Column("input_message_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_t_runs_tenant_id", "t_runs", ["tenant_id"])
    op.create_index("ix_t_runs_conversation_id", "t_runs", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("t_runs")
    op.drop_table("t_messages")
    op.drop_table("t_conversations")
