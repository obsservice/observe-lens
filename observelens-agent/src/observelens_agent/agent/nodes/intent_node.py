from collections.abc import Awaitable, Callable

import structlog

from observelens_agent.agent.intents.recognizer import build_intent_recognizer
from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)

IntentNode = Callable[[AgentState], Awaitable[AgentState]]


def create_intent_node() -> IntentNode:
    async def intent_node(state: AgentState) -> AgentState:
        match = await build_intent_recognizer(state.default_config).recognize(state.msg)
        state.intent_type = match.intent_type
        state.short_cmd = match.short_cmd
        state.entity = match.entity
        state.intent_confidence = match.confidence
        state.intent_reason = match.reason
        state.intent_source = match.source
        logger.info(
            "intent_detected",
            confidence=match.confidence,
            entity=match.entity,
            intent_type=match.intent_type,
            reason=match.reason,
            short_cmd=match.short_cmd,
            source=match.source,
        )
        return state

    return intent_node
