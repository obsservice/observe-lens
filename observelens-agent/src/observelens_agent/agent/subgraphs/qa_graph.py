from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from observelens_agent.agent.nodes.answer_node import AnswerLLM, create_answer_node
from observelens_agent.agent.nodes.rag_node import RAGKnowledgeClient, create_rag_node
from observelens_agent.agent.state.state import AgentState


def build_qa_subgraph(
    knowledge_client: RAGKnowledgeClient | None,
    answer_llm: AnswerLLM | None = None,
) -> CompiledStateGraph[Any]:
    """Build the general documentation and question-answering flow."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)

    graph.add_node("rag", cast(Any, create_rag_node(knowledge_client)))
    graph.add_node("answer", cast(Any, create_answer_node(answer_llm)))

    graph.add_edge(START, "rag")
    graph.add_edge("rag", "answer")
    graph.add_edge("answer", END)

    return graph.compile()
