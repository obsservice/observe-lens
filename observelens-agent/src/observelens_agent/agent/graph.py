from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from observelens_agent.agent.nodes.get_info_node import CatalogEntityClient
from observelens_agent.agent.nodes.get_metric_node import MetricCatalogClient, MetricGatewayClient
from observelens_agent.agent.nodes.intent_node import create_intent_node
from observelens_agent.agent.nodes.rca_node_common import (
    IncidentCatalogClient,
    IncidentGatewayClient,
    IncidentKnowledgeClient,
)
from observelens_agent.agent.state.state import AgentState
from observelens_agent.agent.subgraphs.cmd_graph import CommandGatewayClient, build_cmd_subgraph
from observelens_agent.agent.subgraphs.qa_graph import build_qa_subgraph
from observelens_agent.agent.subgraphs.rca_graph import build_rca_subgraph


def _route_subgraph(state: AgentState) -> str:
    return state.intent_type


def build_agent_graph(
    knowledge_client: IncidentKnowledgeClient | None,
    catalog_client: CatalogEntityClient | MetricCatalogClient | IncidentCatalogClient | None,
    gateway_client: MetricGatewayClient | IncidentGatewayClient | None,
) -> StateGraph[AgentState]:
    """Build the root graph that dispatches requests to domain subgraphs."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)

    graph.add_node("intent", cast(Any, create_intent_node()))

    cmd_subgraph = build_cmd_subgraph(
        catalog_client,
        cast(CommandGatewayClient | None, gateway_client),
    )
    graph.add_node("cmd", cast(Any, cmd_subgraph))

    rca_subgraph = build_rca_subgraph(
        knowledge_client,
        cast(IncidentCatalogClient | None, catalog_client),
        cast(IncidentGatewayClient | None, gateway_client),
    )
    graph.add_node("rca", cast(Any, rca_subgraph))

    qa_subgraph = build_qa_subgraph(knowledge_client)
    graph.add_node("qa", cast(Any, qa_subgraph))

    graph.add_edge(START, "intent")
    graph.add_conditional_edges("intent", _route_subgraph, {"cmd": "cmd", "rca": "rca", "qa": "qa"})
    graph.add_edge("cmd", END)
    graph.add_edge("rca", END)
    graph.add_edge("qa", END)
    return graph
