import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.agent.intents.recognizer import IntentRecognizer
from observelens_agent.agent.nodes.get_info_node import create_get_info_node, extract_entity_id
from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.catalog import CatalogClientError


class FakeCatalogClient:
    def __init__(
        self, entity: dict[str, object] | None = None, error: Exception | None = None
    ) -> None:
        self._entity = entity or {}
        self._error = error
        self.requested_ids: list[str] = []

    async def get_entity(self, entity_id: str) -> dict[str, object]:
        self.requested_ids.append(entity_id)
        if self._error:
            raise self._error
        return self._entity


def test_extract_entity_id_from_web_reference() -> None:
    assert (
        extract_entity_id(
            "/get_info(查看实体详情) @payment [Service/default; entity_id=entity-123]"
        )
        == "entity-123"
    )


def test_extract_entity_id_supports_catalog_qualified_id() -> None:
    assert extract_entity_id("/get_info [entity_id=k8s.cluster:md6s8j7x]") == (
        "k8s.cluster:md6s8j7x"
    )


@pytest.mark.asyncio
async def test_get_info_node_queries_catalog_and_sets_entity_details() -> None:
    entity = {"id": "entity-123", "name": "payment-service", "status": "HEALTHY"}
    catalog = FakeCatalogClient(entity=entity)
    state = AgentState(msg="/get_info @payment [entity_id=entity-123]")

    result = await create_get_info_node(catalog)(state)

    assert catalog.requested_ids == ["entity-123"]
    assert result.entity_details == entity
    assert "payment-service" in result.msg


@pytest.mark.asyncio
async def test_get_info_node_requests_entity_reference_when_missing() -> None:
    catalog = FakeCatalogClient()

    result = await create_get_info_node(catalog)(AgentState(msg="/get_info payment-service"))

    assert catalog.requested_ids == []
    assert result.msg == "请先使用 @ 引用目标实体，再执行 /get_info。"


@pytest.mark.asyncio
async def test_get_info_node_returns_catalog_error_to_user() -> None:
    catalog = FakeCatalogClient(error=CatalogClientError("未找到指定实体"))

    result = await create_get_info_node(catalog)(AgentState(msg="/get_info [entity_id=missing]"))

    assert result.msg == "获取资源详情失败：未找到指定实体"


@pytest.mark.asyncio
async def test_graph_routes_get_info_to_catalog_node() -> None:
    catalog = FakeCatalogClient(entity={"id": "entity-123", "name": "payment-service"})
    graph = build_agent_graph(IntentRecognizer(), catalog).compile()

    result = await graph.ainvoke({"msg": "/get_info [entity_id=entity-123]"})

    assert catalog.requested_ids == ["entity-123"]
    assert result["intent"] == "get_info"
    assert result["entity_details"]["name"] == "payment-service"
