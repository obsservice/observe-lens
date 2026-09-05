from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.get_info_node import CatalogEntityClient, create_get_info_node
from observelens_agent.agent.nodes.get_metric_node import (
    MetricCatalogClient,
    MetricGatewayClient,
    create_get_metric_node,
)
from observelens_agent.agent.nodes.mock_node import mock_node
from observelens_agent.agent.state.state import AgentState


def _route_cmd(state: AgentState) -> str:
    if state.short_cmd == "mock":
        return "mock"
    if state.short_cmd == "get_info":
        return "get_info"
    if state.short_cmd == "get_metric":
        return "get_metric"
    return "unsupported"


def _cmd_router(state: AgentState) -> AgentState:
    return state


def _unsupported_cmd(state: AgentState) -> AgentState:
    state.msg = "当前请求未指定支持的可观测查询命令。"
    return state


def build_cmd_subgraph(
    catalog_client: CatalogEntityClient | MetricCatalogClient | None,
    gateway_client: MetricGatewayClient | None,
) -> CompiledStateGraph[Any]:
    """Build command and common observability-query flows."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("router", cast(Any, _cmd_router))
    graph.add_node("unsupported", cast(Any, _unsupported_cmd))
    graph.add_node("mock", mock_node)
    graph.add_node("get_info", cast(Any, create_get_info_node(catalog_client)))
    graph.add_node(
        "get_metric",
        cast(
            Any,
            create_get_metric_node(
                cast(MetricCatalogClient | None, catalog_client),
                gateway_client,
            ),
        ),
    )
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_cmd,
        {
            "mock": "mock",
            "get_info": "get_info",
            "get_metric": "get_metric",
            "unsupported": "unsupported",
        },
    )
    graph.add_edge("mock", END)
    graph.add_edge("get_info", END)
    graph.add_edge("get_metric", END)
    graph.add_edge("unsupported", END)
    return graph.compile()
