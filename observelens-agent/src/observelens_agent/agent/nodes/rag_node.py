from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.knowledge import KnowledgeClientError

logger = structlog.get_logger(__name__)


class RAGKnowledgeClient(Protocol):
    """Knowledge retrieval dependency used by RAG nodes."""

    async def retrieve_architecture(
        self, query: str, entity_type: str | None, entity_name: str | None
    ) -> list[dict[str, Any]]: ...


RAGNode = Callable[[AgentState], Awaitable[AgentState]]


def _entity_filter(entity: str | None) -> tuple[str | None, str | None]:
    if entity and ":" in entity:
        entity_type, entity_name = entity.split(":", maxsplit=1)
        if entity_type and entity_name:
            return entity_type, entity_name
    return None, entity


def create_rag_node(knowledge_client: RAGKnowledgeClient | None) -> RAGNode:
    """Create a reusable node that retrieves internal knowledge for the current request."""

    async def rag_node(state: AgentState) -> AgentState:
        if knowledge_client is None:
            state.rag_contexts = []
            return state

        entity_type, entity_name = _entity_filter(state.entity)
        try:
            state.rag_contexts = await knowledge_client.retrieve_architecture(
                state.msg,
                entity_type,
                entity_name,
            )
        except KnowledgeClientError as exc:
            logger.warning("rag_retrieval_failed", error=str(exc))
            state.rag_contexts = []
        return state

    return rag_node
