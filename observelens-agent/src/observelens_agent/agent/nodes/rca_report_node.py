import json

from observelens_agent.agent.nodes.rca_node_common import (
    RCA_PIPELINE_STEPS,
    RCAStageNode,
    emit_rca_event,
)
from observelens_agent.agent.state.state import AgentState


def create_report_node() -> RCAStageNode:
    """Create an RCA node that produces the final root-cause report."""

    async def report_node(state: AgentState) -> AgentState:
        emit_rca_event(
            state, "step.started", {"step_id": "report", "title": RCA_PIPELINE_STEPS[4][1]}
        )
        if state.run_failure_message:
            return state
        context, hypothesis = state.rca_context, state.rca_context.get("hypothesis", {})
        report = {
            "entity_id": context.get("entity_id"),
            "entity_name": context.get("entity_name"),
            "architecture_contexts": len(context.get("architecture_contexts", [])),
            "datasets": len(context.get("datasets", [])),
            "topology_nodes": len(context.get("topology", {}).get("nodes", [])),
            "metric_queries": len(context.get("metric_results", [])),
            "log_queries": len(context.get("log_results", [])),
            "anomalies": context.get("anomalies", []),
            "confidence": hypothesis.get("confidence", "低"),
            "root_cause": hypothesis.get("root_cause", "未形成根因结论"),
            "judgement": context.get("judgement", {}),
        }
        state.incident_report = report
        state.msg = "# 根因分析报告\n\n" + json.dumps(report, ensure_ascii=False, indent=2)
        emit_rca_event(state, "output.started", {"format": "markdown"})
        emit_rca_event(state, "output.progress", {"format": "markdown", "content": state.msg})
        emit_rca_event(state, "output.completed", {"format": "markdown", "content": state.msg})
        emit_rca_event(
            state, "step.completed", {"step_id": "report", "summary": "根因分析报告已生成。"}
        )
        return state

    return report_node
