from observelens_agent.agent.nodes.rca_node_common import (
    RCA_PIPELINE_STEPS,
    RCAStageNode,
    anomalies_from_evidence,
    build_hypothesis,
    emit_rca_event,
)
from observelens_agent.agent.state.state import AgentState


def create_hypothesis_node() -> RCAStageNode:
    """Create an RCA node that forms a root-cause hypothesis from evidence."""

    async def hypothesis_node(state: AgentState) -> AgentState:
        emit_rca_event(
            state, "step.started", {"step_id": "hypothesis", "title": RCA_PIPELINE_STEPS[2][1]}
        )
        if state.run_failure_message:
            return state
        anomalies = anomalies_from_evidence(
            state.rca_context.get("metric_results", []), state.rca_context.get("log_results", [])
        )
        confidence, root_cause = build_hypothesis(anomalies)
        state.rca_context.update(
            {
                "anomalies": anomalies,
                "hypothesis": {"confidence": confidence, "root_cause": root_cause},
            }
        )
        emit_rca_event(
            state,
            "finding.generated",
            {
                "id": "rca-hypothesis",
                "category": "issue" if anomalies else "risk",
                "title": "根因假设",
                "analysis": root_cause,
            },
        )
        emit_rca_event(
            state, "step.completed", {"step_id": "hypothesis", "summary": "根因假设已生成。"}
        )
        return state

    return hypothesis_node
