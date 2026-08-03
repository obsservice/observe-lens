"""store investigation events with assistant messages

Revision ID: 20260803_0001
Revises: 20260724_0008
Create Date: 2026-08-03
"""

import sqlalchemy as sa
from alembic import op

revision = "20260803_0001"
down_revision = "20260724_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("t_messages", sa.Column("metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("t_messages", "metadata")
