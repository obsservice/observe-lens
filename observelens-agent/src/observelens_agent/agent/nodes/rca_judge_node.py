from observelens_agent.agent.nodes.rca_node_common import (
    RCA_PIPELINE_STEPS,
    RCAStageNode,
    emit_rca_event,
)
from observelens_agent.agent.state.state import AgentState


def create_judge_node() -> RCAStageNode:
    """Create an RCA node that judges whether the hypothesis is evidence-backed."""

    async def judge_node(state: AgentState) -> AgentState:
        emit_rca_event(
            state, "step.started", {"step_id": "judge", "title": RCA_PIPELINE_STEPS[3][1]}
        )
        if state.run_failure_message:
            return state
        anomalies = state.rca_context.get("anomalies", [])
        judgement = {
            "verdict": "accepted" if isinstance(anomalies, list) and anomalies else "inconclusive",
            "reason": "存在可观测异常证据支持该假设。"
            if isinstance(anomalies, list) and anomalies
            else "缺少足够的可观测异常证据。",
        }
        state.rca_context["judgement"] = judgement
        emit_rca_event(
            state, "step.completed", {"step_id": "judge", "summary": judgement["reason"]}
        )
        return state

    return judge_node
