from datetime import UTC, datetime
from typing import Any

import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.agent.nodes.get_metric_node import (
    MetricDefinition,
    create_get_metric_node,
    extract_metric_definitions,
    render_promql,
    resolve_time_range,
    select_metric_definitions,
)
from observelens_agent.agent.state.state import AgentState

METRIC_SET_ITEMS: list[dict[str, Any]] = [
    {
        "dataset": {
            "document": {
                "kind": "MetricSet",
                "metadata": {"name": "k8s.pod.metric"},
                "spec": {
                    "labels": {"static_keys": [{"name": "namespace"}, {"name": "pod"}]},
                    "metrics": [
                        {
                            "name": "pod_cpu_usage",
                            "description": "CPU usage rate of the Pod.",
                            "generator": (
                                'sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m]))'
                            ),
                            "golden_metric": True,
                            "unit": "core",
                        },
                        {
                            "name": "pod_memory_working_set",
                            "description": "Current working set memory used by the Pod.",
                            "generator": 'sum(container_memory_working_set_bytes{pod!=""})',
                            "golden_metric": True,
                            "unit": "byte",
                        },
                    ],
                },
            }
        }
    }
]


class FakeMetricCatalogClient:
    async def get_entity(self, entity_id: str) -> dict[str, Any]:
        return {
            "__entity_uuid__": entity_id,
            "__fields__": {"id": "prod-api-123", "namespace": "production"},
        }

    async def get_metric_sets(self, entity_id: str) -> list[dict[str, Any]]:
        return METRIC_SET_ITEMS


class FakeMetricGatewayClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, str]] = []

    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]:
        self.requests.append({"query": query, "start": start, "end": end, "step": step})
        return {"summary": "metric result", "data": {"series": []}}


def test_extract_metric_definitions_and_semantic_selection() -> None:
    definitions = extract_metric_definitions(METRIC_SET_ITEMS)

    selected = select_metric_definitions(definitions, "/get_metric 查看 CPU 指标", 3)

    assert [definition.name for definition in selected] == ["pod_cpu_usage"]


def test_render_promql_overrides_only_existing_metric_set_label_matchers() -> None:
    definition = MetricDefinition(
        dataset_name="k8s.pod.metric",
        description="CPU usage",
        golden_metric=True,
        label_names=("namespace", "pod", "node", "ip"),
        name="pod_cpu_usage",
        promql='sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m]))',
        unit="core",
    )

    query = render_promql(
        definition, {"__fields__": {"namespace": "production", "id": "prod-api-123"}}
    )

    assert 'pod="prod-api-123"' in query
    assert 'pod!=""' not in query
    assert 'namespace="production"' not in query
    assert "node=" not in query
    assert "ip=" not in query


def test_resolve_time_range_uses_requested_duration() -> None:
    end = datetime(2026, 8, 31, 12, tzinfo=UTC)
    start, resolved_end = resolve_time_range("最近 30 分钟 CPU", 60, now=end)

    assert start == "2026-08-31T11:30:00+00:00"
    assert resolved_end == "2026-08-31T12:00:00+00:00"


@pytest.mark.asyncio
async def test_get_metric_node_queries_catalog_then_gateway() -> None:
    catalog = FakeMetricCatalogClient()
    gateway = FakeMetricGatewayClient()
    node = create_get_metric_node(catalog, gateway)

    state = await node(
        AgentState(msg="/get_metric(查看指标) CPU 最近 30 分钟 [entity_id=k8s.pod:prod-api-123]")
    )

    assert len(gateway.requests) == 1
    assert gateway.requests[0]["step"] == "60s"
    assert 'pod="prod-api-123"' in gateway.requests[0]["query"]
    assert state.metric_results[0]["metric"] == "pod_cpu_usage"


@pytest.mark.asyncio
async def test_graph_routes_get_metric_to_metric_node() -> None:
    catalog = FakeMetricCatalogClient()
    gateway = FakeMetricGatewayClient()
    graph = build_agent_graph(None, catalog, gateway).compile()

    result = await graph.ainvoke({"msg": "/get_metric CPU [entity_id=k8s.pod:prod-api-123]"})

    assert result["intent_type"] == "cmd"
    assert result["metric_results"][0]["metric"] == "pod_cpu_usage"
