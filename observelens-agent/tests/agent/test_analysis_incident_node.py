import json
from typing import Any

import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.services.runs.router import extract_sse_event

DATASETS: list[dict[str, Any]] = [
    {
        "dataset": {
            "document": {
                "kind": "MetricSet",
                "metadata": {"name": "k8s.pod.metric"},
                "spec": {
                    "labels": {"static_keys": [{"name": "pod"}]},
                    "metrics": [
                        {
                            "name": "pod_cpu_usage",
                            "description": "CPU usage rate of the Pod.",
                            "generator": (
                                'sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m]))'
                            ),
                            "golden_metric": True,
                            "unit": "core",
                        }
                    ],
                },
            }
        }
    }
]


class FakeIncidentCatalogClient:
    async def get_entity(self, entity_id: str) -> dict[str, Any]:
        return {
            "__entity_uuid__": entity_id,
            "__entity_type__": "k8s.pod",
            "__fields__": {
                "display_name": "prod-api-123",
                "id": "prod-api-123",
                "namespace": "production",
            },
        }

    async def search_entities(self, keyword: str, limit: int = 5) -> list[dict[str, Any]]:
        return [await self.get_entity("k8s.pod:prod-api-123")]

    async def get_datasets(self, entity_id: str, dataset_type: str = "all") -> list[dict[str, Any]]:
        return DATASETS

    async def get_topology(self, entity_id: str, depth: int = 3) -> dict[str, Any]:
        return {"root_entity_id": entity_id, "nodes": [{"id": entity_id}], "edges": []}


class FakeKnowledgeClient:
    async def retrieve_architecture(
        self, query: str, entity_type: str | None, entity_name: str | None
    ) -> list[dict[str, Any]]:
        return [
            {
                "score": 0.92,
                "content": "prod-api is called by gateway and depends on orders-db.",
                "citation": {"document_name": "prod-api architecture"},
            }
        ]


class FakeIncidentGatewayClient:
    def __init__(self) -> None:
        self.metric_requests: list[str] = []
        self.log_requests: list[str] = []

    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]:
        self.metric_requests.append(query)
        return {"summary": "one series", "data": {"series_count": 1}, "evidence": []}

    async def query_logs(
        self, query: str, start: str, end: str, limit: int = 200
    ) -> dict[str, Any]:
        self.log_requests.append(query)
        return {
            "summary": "one error log",
            "data": {"total_lines": 1},
            "evidence": [{"value": "ERROR database timeout while connecting to orders-db"}],
        }


@pytest.mark.asyncio
async def test_analysis_incident_streams_all_investigation_steps() -> None:
    catalog = FakeIncidentCatalogClient()
    knowledge = FakeKnowledgeClient()
    gateway = FakeIncidentGatewayClient()
    graph = build_agent_graph(knowledge, catalog, gateway).compile()

    events: list[dict[str, Any]] = []
    async for _, mode, data in graph.astream(
        {
            "msg": "/analysis_incident 数据库超时 [entity_id=k8s.pod:prod-api-123]",
            "conversation_id": "conversation-1",
            "run_id": "run-1",
        },
        stream_mode=["custom", "values"],
        subgraphs=True,
    ):
        if mode == "custom" and isinstance(data, dict):
            sse = extract_sse_event(data)
            if sse:
                events.append(json.loads(sse.split("data: ", maxsplit=1)[1]))

    event_types = [event["type"] for event in events]
    started_steps = [
        event["data"]["step_id"] for event in events if event["type"] == "step.started"
    ]
    completed_steps = [
        event["data"]["step_id"] for event in events if event["type"] == "step.completed"
    ]

    assert event_types[0] == "analysis.generated"
    assert "plan.generated" in event_types
    assert started_steps == [
        "identify_entity",
        "learn_architecture",
        "load_semantics",
        "plan_telemetry",
        "fetch_telemetry",
        "detect_anomalies",
        "infer_root_cause",
        "build_report",
    ]
    assert completed_steps == started_steps
    assert "finding.generated" in event_types
    assert event_types[-1] == "step.completed"
    assert "output.completed" in event_types
    assert len(gateway.metric_requests) == 1
    assert len(gateway.log_requests) == 1


@pytest.mark.asyncio
async def test_analysis_incident_uses_catalog_search_when_entity_is_not_referenced() -> None:
    catalog = FakeIncidentCatalogClient()
    gateway = FakeIncidentGatewayClient()
    graph = build_agent_graph(FakeKnowledgeClient(), catalog, gateway).compile()

    result = await graph.ainvoke({"msg": "/analysis_incident prod-api 数据库超时"})

    assert result["intent_type"] == "rca"
    assert result["incident_report"]["entity_id"] == "k8s.pod:prod-api-123"
    assert "应用或依赖调用失败" in result["msg"]
