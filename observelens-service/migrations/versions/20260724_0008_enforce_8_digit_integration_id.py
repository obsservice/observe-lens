"""enforce 8-digit incident integration id

Revision ID: 20260724_0008
Revises: 20260724_0007
Create Date: 2026-07-24
"""

from alembic import op

revision = "20260724_0008"
down_revision = "20260724_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE t_incident_integrations SET id = -id WHERE id > 0")
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                10000000 + ROW_NUMBER() OVER (ORDER BY create_time, ABS(id)) - 1 AS new_id
            FROM t_incident_integrations
        )
        UPDATE t_incident_integrations AS integration
        SET id = ranked.new_id
        FROM ranked
        WHERE integration.id = ranked.id
        """
    )
    op.create_check_constraint(
        "ck_incident_integration_id_8_digits",
        "t_incident_integrations",
        "id BETWEEN 10000000 AND 99999999",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_incident_integration_id_8_digits",
        "t_incident_integrations",
        type_="check",
    )
