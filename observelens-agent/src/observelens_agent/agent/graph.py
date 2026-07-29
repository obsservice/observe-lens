from langgraph.graph import END, START, StateGraph

from observelens_agent.agent.nodes.tracing_node import tracing_node
from observelens_agent.agent.state.state import AgentState


def build_agent_graph() -> StateGraph[AgentState]:
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("tracing", tracing_node)
    graph.add_edge(START, "tracing")
    graph.add_edge("tracing", END)
    return graph
