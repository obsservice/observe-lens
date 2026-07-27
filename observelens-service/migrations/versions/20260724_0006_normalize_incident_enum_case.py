"""normalize incident enum case

Revision ID: 20260724_0006
Revises: 20260724_0005
Create Date: 2026-07-24
"""

from alembic import op

revision = "20260724_0006"
down_revision = "20260724_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE t_incident_integrations SET type = 'Alertmanager' WHERE type = 'AlertManager'"
    )
    op.execute("UPDATE t_incident_integrations SET type = 'Opsgenie' WHERE type = 'OpsGenie'")
    op.execute("UPDATE t_incident_integrations SET status = 'Enabled' WHERE status = 'ENABLED'")
    op.execute("UPDATE t_incident_integrations SET status = 'Disabled' WHERE status = 'DISABLED'")
    op.execute("UPDATE t_incidents SET source = 'Webhook' WHERE source IN ('MANUAL', 'WEBHOOK')")
    op.execute("UPDATE t_incidents SET source = 'Alertmanager' WHERE source = 'ALERTMANAGER'")
    op.execute("UPDATE t_incidents SET source = 'Grafana' WHERE source = 'GRAFANA'")


def downgrade() -> None:
    op.execute("UPDATE t_incidents SET source = 'WEBHOOK' WHERE source = 'Webhook'")
    op.execute("UPDATE t_incidents SET source = 'ALERTMANAGER' WHERE source = 'Alertmanager'")
    op.execute("UPDATE t_incidents SET source = 'GRAFANA' WHERE source = 'Grafana'")
    op.execute("UPDATE t_incident_integrations SET status = 'ENABLED' WHERE status = 'Enabled'")
    op.execute("UPDATE t_incident_integrations SET status = 'DISABLED' WHERE status = 'Disabled'")
    op.execute(
        "UPDATE t_incident_integrations SET type = 'AlertManager' WHERE type = 'Alertmanager'"
    )
    op.execute("UPDATE t_incident_integrations SET type = 'OpsGenie' WHERE type = 'Opsgenie'")
