import json
from collections.abc import Awaitable, Callable
from typing import Any

from observelens_agent.agent.state.state import AgentState

GenerateIncidentReportNode = Callable[[AgentState], Awaitable[AgentState]]


def _build_report(state: AgentState) -> dict[str, Any]:
    return {
        "incident": state.incident,
        "entity_details": state.entity_details,
        "metric_results": state.metric_results,
        "log_results": state.log_results,
        "trace_result": state.trace_result,
        "event_results": state.event_results,
        "rag_contexts": state.rag_contexts,
    }


def create_generate_incident_report_node() -> GenerateIncidentReportNode:
    """Create a reusable node that assembles collected investigation evidence into a report."""

    async def generate_incident_report_node(state: AgentState) -> AgentState:
        state.incident_report = _build_report(state)
        state.msg = (
            "故障报告：\n```json\n"
            + json.dumps(state.incident_report, ensure_ascii=False, indent=2)
            + "\n```"
        )
        return state

    return generate_incident_report_node
