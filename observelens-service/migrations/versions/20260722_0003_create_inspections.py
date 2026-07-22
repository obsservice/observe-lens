"""create inspection tables

Revision ID: 20260722_0003
Revises: 20260722_0002
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260722_0003"
down_revision = "20260722_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "t_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(128), nullable=False),
        sa.Column("input_template", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
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
        sa.UniqueConstraint("tenant_id", "name", name="uq_task_tenant_name"),
    )
    op.create_index("ix_t_tasks_tenant_id", "t_tasks", ["tenant_id"])
    op.create_table(
        "t_task_schedules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("t_tasks.id"), nullable=False),
        sa.Column("schedule_type", sa.String(16), nullable=False),
        sa.Column("cron_expression", sa.String(128), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_t_task_schedules_tenant_task", "t_task_schedules", ["tenant_id", "task_id"])
    op.create_table(
        "t_task_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("t_tasks.id"), nullable=False),
        sa.Column("schedule_id", sa.BigInteger(), nullable=True),
        sa.Column("trigger_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_t_task_runs_tenant_task", "t_task_runs", ["tenant_id", "task_id"])


def downgrade() -> None:
    op.drop_table("t_task_runs")
    op.drop_table("t_task_schedules")
    op.drop_table("t_tasks")
