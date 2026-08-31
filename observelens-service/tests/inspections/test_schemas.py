from datetime import UTC, datetime
from types import SimpleNamespace

from observelens_service.modules.inspections.schemas import (
    InspectionExecutionResponse,
    InspectionResponse,
)
from observelens_service.modules.inspections.service import InspectionService


def test_inspection_response_accepts_persistence_timestamp_aliases() -> None:
    timestamp = datetime.now(UTC)
    response = InspectionResponse(
        id=1,
        name="Daily Cluster Health",
        description=None,
        scope="Kubernetes",
        schedule="Every Day",
        status="ENABLED",
        create_time=timestamp,
        update_time=timestamp,
    )
    assert response.created_at == timestamp
    assert response.updated_at == timestamp


def test_execution_response_reports_running_status() -> None:
    response = InspectionExecutionResponse(run_id=1001, status="RUNNING")

    assert response.status == "RUNNING"


def test_execution_content_renders_scope_and_agent_command() -> None:
    task = SimpleNamespace(
        name="Production API health check",
        scope="production/api",
        input_template="Inspect {{scope}} for availability and error signals.",
    )

    content = InspectionService._render_agent_content(task)

    assert content == (
        "/analysis_incident 巡检任务 Production API health check："
        "Inspect production/api for availability and error signals."
    )
