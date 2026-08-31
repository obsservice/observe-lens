from observelens_agent.clients.catalog import CatalogClient


def test_catalog_client_uses_workspace_and_encodes_entity_id() -> None:
    client = CatalogClient(
        base_url="http://localhost:3083/",
        timeout_seconds=10,
        workspace_id="ws000003",
    )

    assert client._base_url == "http://localhost:3083"
    assert client._workspace_id == "ws000003"
    assert client._entity_url("k8s.cluster:md6s8j7x") == (
        "http://localhost:3083/api/v1/workspaces/ws000003/entities/k8s.cluster%3Amd6s8j7x"
    )


def test_catalog_client_unwraps_catalog_data_response() -> None:
    payload = {
        "code": 0,
        "msg": "success",
        "data": {"__entity_uuid__": "k8s.cluster:md6s8j7x", "__fields__": {"status": "running"}},
    }

    entity = CatalogClient._unwrap_entity_response(payload)

    assert entity["__entity_uuid__"] == "k8s.cluster:md6s8j7x"
