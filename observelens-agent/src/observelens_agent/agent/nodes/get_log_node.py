import json
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from observelens_agent.agent.nodes.get_metric_node import resolve_time_range
from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.mcp_gateway import MCPGatewayClientError

logger = structlog.get_logger(__name__)


class LogGatewayClient(Protocol):
    """Gateway dependency used by log-query nodes."""

    async def query_logs(
        self, query: str, start: str, end: str, limit: int = 200
    ) -> dict[str, Any]: ...


GetLogNode = Callable[[AgentState], Awaitable[AgentState]]


def _extract_logql(content: str) -> str | None:
    command, _, query = content.partition(" ")
    if not command.startswith("/get_log"):
        return None
    normalized_query = query.strip()
    return normalized_query or None


def create_get_log_node(gateway_client: LogGatewayClient | None) -> GetLogNode:
    """Create a reusable node that queries Loki with a user-provided LogQL expression."""

    async def get_log_node(state: AgentState) -> AgentState:
        query = _extract_logql(state.msg)
        if query is None:
            state.msg = "请在 /get_log 后提供 LogQL 查询表达式。"
            return state
        if gateway_client is None:
            state.msg = "日志查询依赖未配置，暂时无法获取日志数据。"
            return state

        start, end = resolve_time_range(
            state.msg,
            state.default_config.metric_query_default_window_minutes,
        )
        try:
            state.log_results = await gateway_client.query_logs(
                query,
                start=start,
                end=end,
                limit=state.default_config.incident_log_query_limit,
            )
        except MCPGatewayClientError as exc:
            logger.warning("get_log_failed", error=str(exc), query=query)
            state.msg = f"日志查询失败：{exc}"
            return state
        state.msg = (
            "日志查询结果：\n```json\n"
            + json.dumps(state.log_results, ensure_ascii=False, indent=2)
            + "\n```"
        )
        return state

    return get_log_node
