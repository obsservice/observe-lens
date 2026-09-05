import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.mcp_gateway import MCPGatewayClientError

logger = structlog.get_logger(__name__)

_TRACE_ID_PATTERN = re.compile(r"\btrace_id\s*[=:]\s*([A-Za-z0-9_-]+)", re.IGNORECASE)


class TraceGatewayClient(Protocol):
    """Gateway dependency used by trace-query nodes."""

    async def get_trace(self, trace_id: str) -> dict[str, Any]: ...


GetTraceNode = Callable[[AgentState], Awaitable[AgentState]]


def _extract_trace_id(content: str) -> str | None:
    if match := _TRACE_ID_PATTERN.search(content):
        return match.group(1)
    command, _, argument = content.partition(" ")
    if command.startswith("/get_tarce") and argument.strip():
        return argument.strip()
    return None


def create_get_trace_node(gateway_client: TraceGatewayClient | None) -> GetTraceNode:
    """Create a reusable node that retrieves a trace by its ID."""

    async def get_trace_node(state: AgentState) -> AgentState:
        trace_id = _extract_trace_id(state.msg)
        if trace_id is None:
            state.msg = "请在 /get_tarce 后提供 trace_id。"
            return state
        if gateway_client is None:
            state.msg = "链路追踪查询依赖未配置，暂时无法获取 Trace 数据。"
            return state

        try:
            state.trace_result = await gateway_client.get_trace(trace_id)
        except MCPGatewayClientError as exc:
            logger.warning("get_trace_failed", error=str(exc), trace_id=trace_id)
            state.msg = f"链路追踪查询失败：{exc}"
            return state
        state.msg = (
            "链路追踪查询结果：\n```json\n"
            + json.dumps(state.trace_result, ensure_ascii=False, indent=2)
            + "\n```"
        )
        return state

    return get_trace_node
