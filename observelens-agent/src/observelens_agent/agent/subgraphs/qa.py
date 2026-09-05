from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.tracing_node import tracing_node
from observelens_agent.agent.state.state import AgentState


def build_qa_subgraph() -> CompiledStateGraph[Any]:
    """Build the general documentation and question-answering flow."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("answer", cast(Any, tracing_node))
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)
    return graph.compile()
