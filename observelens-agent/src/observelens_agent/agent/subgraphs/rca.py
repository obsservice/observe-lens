from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.analysis_incident_node import (
    IncidentCatalogClient,
    IncidentGatewayClient,
    IncidentKnowledgeClient,
    create_analysis_incident_node,
)
from observelens_agent.agent.state.state import AgentState


def build_rca_subgraph(
    knowledge_client: IncidentKnowledgeClient | None,
    catalog_client: IncidentCatalogClient | None,
    gateway_client: IncidentGatewayClient | None,
) -> CompiledStateGraph[Any]:
    """Build root-cause analysis flows."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node(
        "analysis_incident",
        cast(
            Any,
            create_analysis_incident_node(
                catalog_client,
                knowledge_client,
                gateway_client,
            ),
        ),
    )
    graph.add_edge(START, "analysis_incident")
    graph.add_edge("analysis_incident", END)
    return graph.compile()
