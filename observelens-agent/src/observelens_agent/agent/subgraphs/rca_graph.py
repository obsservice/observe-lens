from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.rca_evidence_node import create_evidence_node
from observelens_agent.agent.nodes.rca_hypothesis_node import create_hypothesis_node
from observelens_agent.agent.nodes.rca_judge_node import create_judge_node
from observelens_agent.agent.nodes.rca_node_common import (
    IncidentCatalogClient,
    IncidentGatewayClient,
    IncidentKnowledgeClient,
)
from observelens_agent.agent.nodes.rca_planner_node import create_planner_node
from observelens_agent.agent.nodes.rca_report_node import create_report_node
from observelens_agent.agent.state.state import AgentState


def build_rca_subgraph(
    knowledge_client: IncidentKnowledgeClient | None,
    catalog_client: IncidentCatalogClient | None,
    gateway_client: IncidentGatewayClient | None,
) -> CompiledStateGraph[Any]:
    """Build root-cause analysis flows."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)

    graph.add_node("planner", cast(Any, create_planner_node(catalog_client, knowledge_client)))
    graph.add_node("evidence", cast(Any, create_evidence_node(gateway_client)))
    graph.add_node("hypothesis", cast(Any, create_hypothesis_node()))
    graph.add_node("judge", cast(Any, create_judge_node()))
    graph.add_node("report", cast(Any, create_report_node()))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "evidence")
    graph.add_edge("evidence", "hypothesis")
    graph.add_edge("hypothesis", "judge")
    graph.add_edge("judge", "report")
    graph.add_edge("report", END)
    return graph.compile()
