"""add incident integration type

Revision ID: 20260724_0003
Revises: 20260722_0002
Create Date: 2026-07-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0003"
down_revision = "20260722_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "t_incident_integrations",
        sa.Column(
            "type",
            sa.String(length=32),
            server_default="Webhook",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("t_incident_integrations", "type")
