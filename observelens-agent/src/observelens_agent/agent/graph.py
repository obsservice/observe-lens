from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from observelens_agent.agent.intents.recognizer import IntentRecognizer
from observelens_agent.agent.nodes.get_info_node import CatalogEntityClient, create_get_info_node
from observelens_agent.agent.nodes.get_metric_node import (
    MetricCatalogClient,
    MetricGatewayClient,
    create_get_metric_node,
)
from observelens_agent.agent.nodes.intent_node import create_intent_node
from observelens_agent.agent.nodes.mock_node import mock_node
from observelens_agent.agent.nodes.tracing_node import tracing_node
from observelens_agent.agent.state.state import AgentState


def _route_intent(state: AgentState) -> str:
    if state.intent == "mock":
        return "mock"
    if state.intent == "get_info":
        return "get_info"
    if state.intent == "get_metric":
        return "get_metric"
    return "agent"


def build_agent_graph(
    intent_recognizer: IntentRecognizer | None = None,
    catalog_client: CatalogEntityClient | None = None,
    metric_catalog_client: MetricCatalogClient | None = None,
    metric_gateway_client: MetricGatewayClient | None = None,
    metric_query_default_window_minutes: int = 60,
    metric_query_step: str = "60s",
    metric_query_limit: int = 3,
) -> StateGraph[AgentState]:
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("intent", cast(Any, create_intent_node(intent_recognizer or IntentRecognizer())))
    graph.add_node("get_info", cast(Any, create_get_info_node(catalog_client)))
    graph.add_node(
        "get_metric",
        cast(
            Any,
            create_get_metric_node(
                metric_catalog_client or cast(MetricCatalogClient | None, catalog_client),
                metric_gateway_client,
                metric_query_default_window_minutes,
                metric_query_step,
                metric_query_limit,
            ),
        ),
    )
    graph.add_node("mock", mock_node)
    graph.add_node("tracing", tracing_node)

    graph.add_edge(START, "intent")
    graph.add_conditional_edges(
        "intent",
        _route_intent,
        {"mock": "mock", "get_info": "get_info", "get_metric": "get_metric", "agent": "tracing"},
    )
    graph.add_edge("get_info", END)
    graph.add_edge("get_metric", END)
    graph.add_edge("mock", END)
    graph.add_edge("tracing", END)
    return graph
