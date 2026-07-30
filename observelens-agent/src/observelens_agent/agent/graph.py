from langgraph.graph import END, START, StateGraph

from observelens_agent.agent.nodes.intent_node import intent_node
from observelens_agent.agent.nodes.mock_node import mock_node
from observelens_agent.agent.nodes.tracing_node import tracing_node
from observelens_agent.agent.state.state import AgentState


def _route_intent(state: AgentState) -> str:
    return state.intent


def build_agent_graph() -> StateGraph[AgentState]:
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("intent", intent_node)
    graph.add_node("mock", mock_node)
    graph.add_node("tracing", tracing_node)

    graph.add_edge(START, "intent")
    graph.add_conditional_edges("intent", _route_intent, {"mock": "mock", "agent": "tracing"})
    graph.add_edge("mock", END)
    graph.add_edge("tracing", END)
    return graph
