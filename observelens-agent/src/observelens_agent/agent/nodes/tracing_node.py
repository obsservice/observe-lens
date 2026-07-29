import structlog

from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)


def tracing_node(state: AgentState) -> AgentState:
    logger.info("tracing_msg", msg=state.msg, incident=state.incident)
    state.msg = "Hi, " + state.msg
    return state
