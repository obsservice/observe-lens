from typing import Any

import pytest

from observelens_agent.agent.nodes.generate_incident_report_node import (
    create_generate_incident_report_node,
)
from observelens_agent.agent.nodes.get_event_node import create_get_event_node
from observelens_agent.agent.nodes.get_log_node import create_get_log_node
from observelens_agent.agent.nodes.get_trace_node import create_get_trace_node
from observelens_agent.agent.state.state import AgentState


class FakeCommandGatewayClient:
    def __init__(self) -> None:
        self.log_calls: list[dict[str, object]] = []
        self.trace_calls: list[str] = []
        self.event_calls: list[dict[str, object]] = []

    async def query_logs(
        self, query: str, start: str, end: str, limit: int = 200
    ) -> dict[str, Any]:
        self.log_calls.append({"query": query, "start": start, "end": end, "limit": limit})
        return {"summary": "one error log"}

    async def get_trace(self, trace_id: str) -> dict[str, Any]:
        self.trace_calls.append(trace_id)
        return {"trace_id": trace_id, "spans": []}

    async def get_events(
        self,
        cluster: str,
        namespace: str | None = None,
        field_selector: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        self.event_calls.append(
            {
                "cluster": cluster,
                "namespace": namespace,
                "field_selector": field_selector,
                "limit": limit,
            }
        )
        return {"events": []}


@pytest.mark.asyncio
async def test_get_log_node_queries_gateway_with_logql() -> None:
    gateway = FakeCommandGatewayClient()
    state = await create_get_log_node(gateway)(
        AgentState(msg='/get_log {app="payment-service"} |= "error"')
    )

    assert gateway.log_calls[0]["query"] == '{app="payment-service"} |= "error"'
    assert state.log_results == {"summary": "one error log"}
    assert state.msg.startswith("日志查询结果：")


@pytest.mark.asyncio
async def test_get_trace_node_queries_gateway_with_trace_id() -> None:
    gateway = FakeCommandGatewayClient()
    state = await create_get_trace_node(gateway)(AgentState(msg="/get_tarce trace_id=trace-123"))

    assert gateway.trace_calls == ["trace-123"]
    assert state.trace_result == {"trace_id": "trace-123", "spans": []}
    assert state.msg.startswith("链路追踪查询结果：")


@pytest.mark.asyncio
async def test_get_event_node_queries_gateway_with_cluster_and_namespace() -> None:
    gateway = FakeCommandGatewayClient()
    state = await create_get_event_node(gateway)(
        AgentState(msg="/get_event cluster=prod namespace=payments")
    )

    assert gateway.event_calls == [
        {"cluster": "prod", "namespace": "payments", "field_selector": None, "limit": 50}
    ]
    assert state.event_results == {"events": []}
    assert state.msg.startswith("Kubernetes 事件查询结果：")


@pytest.mark.asyncio
async def test_generate_incident_report_node_collects_available_evidence() -> None:
    state = await create_generate_incident_report_node()(
        AgentState(
            msg="/generate_incident_report",
            incident={"title": "payment latency"},
            metric_results=[{"metric": "latency"}],
            log_results={"summary": "timeout"},
        )
    )

    assert state.incident_report == {
        "incident": {"title": "payment latency"},
        "entity_details": None,
        "metric_results": [{"metric": "latency"}],
        "log_results": {"summary": "timeout"},
        "trace_result": None,
        "event_results": None,
        "rag_contexts": [],
    }
    assert state.msg.startswith("故障报告：")
