from datetime import UTC, datetime

from observelens_service.modules.inspections.schemas import InspectionResponse


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
