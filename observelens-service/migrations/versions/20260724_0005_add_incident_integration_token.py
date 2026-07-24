"""add incident integration token

Revision ID: 20260724_0005
Revises: 20260724_0004
Create Date: 2026-07-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0005"
down_revision = "20260724_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "t_incident_integrations",
        sa.Column("token", sa.String(length=128), nullable=True),
    )
    op.execute("UPDATE t_incident_integrations SET token = token_hint WHERE token IS NULL")
    op.alter_column("t_incident_integrations", "token", nullable=False)


def downgrade() -> None:
    op.drop_column("t_incident_integrations", "token")
