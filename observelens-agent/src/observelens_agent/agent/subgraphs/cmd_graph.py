from typing import Any, Protocol, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.generate_incident_report_node import (
    create_generate_incident_report_node,
)
from observelens_agent.agent.nodes.get_event_node import EventGatewayClient, create_get_event_node
from observelens_agent.agent.nodes.get_info_node import CatalogEntityClient, create_get_info_node
from observelens_agent.agent.nodes.get_log_node import LogGatewayClient, create_get_log_node
from observelens_agent.agent.nodes.get_metric_node import (
    MetricCatalogClient,
    MetricGatewayClient,
    create_get_metric_node,
)
from observelens_agent.agent.nodes.get_trace_node import TraceGatewayClient, create_get_trace_node
from observelens_agent.agent.state.state import AgentState


class CommandGatewayClient(
    MetricGatewayClient,
    LogGatewayClient,
    TraceGatewayClient,
    EventGatewayClient,
    Protocol,
):
    """Gateway capabilities required by the CMD subgraph."""


def _route_cmd(state: AgentState) -> str:
    if state.short_cmd == "get_entity_info":
        return "get_entity_info"
    if state.short_cmd == "get_metric":
        return "get_metric"
    if state.short_cmd in {
        "get_log",
        "get_tarce",
        "get_event",
        "generate_incident_report",
    }:
        return state.short_cmd
    return "unsupported"


def _cmd_router(state: AgentState) -> AgentState:
    return state


def _unsupported_cmd(state: AgentState) -> AgentState:
    state.msg = "当前请求未指定支持的可观测查询命令。"
    return state


def build_cmd_subgraph(
    catalog_client: CatalogEntityClient | MetricCatalogClient | None,
    gateway_client: CommandGatewayClient | None,
) -> CompiledStateGraph[Any]:
    """Build command and common observability-query flows."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)

    graph.add_node("router", cast(Any, _cmd_router))
    graph.add_node("unsupported", cast(Any, _unsupported_cmd))

    graph.add_node("get_entity_info", cast(Any, create_get_info_node(catalog_client)))
    graph.add_node("get_metric", cast(Any, create_get_metric_node(catalog_client, gateway_client )))
    graph.add_node("get_log", cast(Any, create_get_log_node(gateway_client)))
    graph.add_node("get_tarce", cast(Any, create_get_trace_node(gateway_client)))
    graph.add_node("get_event", cast(Any, create_get_event_node(gateway_client)))
    graph.add_node("generate_incident_report", cast(Any, create_generate_incident_report_node()))

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_cmd,
        {
            "get_entity_info": "get_entity_info",
            "get_metric": "get_metric",
            "get_log": "get_log",
            "get_tarce": "get_tarce",
            "get_event": "get_event",
            "generate_incident_report": "generate_incident_report",
            "unsupported": "unsupported",
        },
    )
    graph.add_edge("get_entity_info", END)
    graph.add_edge("get_metric", END)
    graph.add_edge("get_log", END)
    graph.add_edge("get_tarce", END)
    graph.add_edge("get_event", END)
    graph.add_edge("generate_incident_report", END)
    graph.add_edge("unsupported", END)
    return graph.compile()
