from collections.abc import Awaitable, Callable

import structlog

from observelens_agent.agent.intents.recognizer import IntentRecognizer
from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)

IntentNode = Callable[[AgentState], Awaitable[AgentState]]


def create_intent_node(recognizer: IntentRecognizer) -> IntentNode:
    async def intent_node(state: AgentState) -> AgentState:
        match = await recognizer.recognize(state.msg)
        state.intent = match.intent
        state.intent_confidence = match.confidence
        state.intent_reason = match.reason
        state.intent_source = match.source
        logger.info(
            "intent_detected",
            confidence=match.confidence,
            intent=match.intent,
            reason=match.reason,
            source=match.source,
        )
        return state

    return intent_node
