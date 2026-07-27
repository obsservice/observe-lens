"""limit incident integration types

Revision ID: 20260724_0007
Revises: 20260724_0006
Create Date: 2026-07-24
"""

from alembic import op

revision = "20260724_0007"
down_revision = "20260724_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE t_incident_integrations
        SET type = 'Webhook'
        WHERE type NOT IN ('Webhook', 'Alertmanager')
        """
    )
    op.execute(
        """
        UPDATE t_incidents
        SET source = 'Webhook'
        WHERE source IS NOT NULL AND source NOT IN ('Webhook', 'Alertmanager')
        """
    )


def downgrade() -> None:
    pass
