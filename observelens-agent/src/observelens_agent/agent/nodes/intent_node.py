import structlog

from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)

_MOCK_KEYWORDS = ("mock", "demo", "样例", "演示", "假数据")


def intent_node(state: AgentState) -> AgentState:
    """Detect whether the user is requesting mock/demo data."""
    content_lower = state.msg.lower()
    if any(kw in content_lower for kw in _MOCK_KEYWORDS):
        state.intent = "mock"
    else:
        state.intent = "agent"

    logger.info("intent_detected", intent=state.intent, msg=state.msg)
    return state
