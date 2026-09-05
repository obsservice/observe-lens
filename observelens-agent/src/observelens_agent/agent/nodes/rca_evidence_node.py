import asyncio
from typing import Any

from observelens_agent.agent.nodes.get_metric_node import resolve_time_range
from observelens_agent.agent.nodes.rca_node_common import (
    RCA_PIPELINE_STEPS,
    IncidentGatewayClient,
    RCAStageNode,
    emit_rca_event,
)
from observelens_agent.agent.state.state import AgentState


def create_evidence_node(gateway_client: IncidentGatewayClient | None) -> RCAStageNode:
    """Create an RCA evidence collector for planned metric and log queries."""

    async def evidence_node(state: AgentState) -> AgentState:
        emit_rca_event(
            state, "step.started", {"step_id": "evidence", "title": RCA_PIPELINE_STEPS[1][1]}
        )
        if state.run_failure_message:
            return state
        metric_queries = state.rca_context.get("metric_queries", [])
        log_queries = state.rca_context.get("log_queries", [])
        metric_results: list[dict[str, Any]] = []
        log_results: list[dict[str, Any]] = []
        if (
            gateway_client is not None
            and isinstance(metric_queries, list)
            and isinstance(log_queries, list)
        ):
            start, end = resolve_time_range(
                state.msg, state.default_config.metric_query_default_window_minutes
            )
            metric_values = await asyncio.gather(
                *(
                    gateway_client.range_query(
                        item["query"], start, end, state.default_config.metric_query_step
                    )
                    for item in metric_queries
                ),
                return_exceptions=True,
            )
            for item, value in zip(metric_queries, metric_values, strict=True):
                metric_results.append(
                    {**item, "error": str(value)}
                    if isinstance(value, Exception)
                    else {**item, "result": value}
                )
            log_values = await asyncio.gather(
                *(
                    gateway_client.query_logs(
                        query, start, end, state.default_config.incident_log_query_limit
                    )
                    for query in log_queries
                ),
                return_exceptions=True,
            )
            for query, value in zip(log_queries, log_values, strict=True):
                log_results.append(
                    {"query": query, "error": str(value)}
                    if isinstance(value, Exception)
                    else {"query": query, "result": value}
                )
        state.metric_results = metric_results
        state.log_results = {"results": log_results}
        state.rca_context.update({"metric_results": metric_results, "log_results": log_results})
        emit_rca_event(
            state,
            "observation.generated",
            {
                "id": "rca-evidence",
                "observation_type": "json",
                "title": "可观测证据",
                "content": {"metrics": metric_results, "logs": log_results},
            },
        )
        emit_rca_event(
            state,
            "step.completed",
            {
                "step_id": "evidence",
                "summary": f"收集到 {len(metric_results)} 项指标和 {len(log_results)} 条日志证据。",
            },
        )
        return state

    return evidence_node
