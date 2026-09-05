import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.mcp_gateway import MCPGatewayClientError

logger = structlog.get_logger(__name__)

_CLUSTER_PATTERN = re.compile(r"\bcluster\s*[=:]\s*([A-Za-z0-9_.-]+)", re.IGNORECASE)
_NAMESPACE_PATTERN = re.compile(r"\bnamespace\s*[=:]\s*([A-Za-z0-9_.-]+)", re.IGNORECASE)


class EventGatewayClient(Protocol):
    """Gateway dependency used by Kubernetes event-query nodes."""

    async def get_events(
        self,
        cluster: str,
        namespace: str | None = None,
        field_selector: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]: ...


GetEventNode = Callable[[AgentState], Awaitable[AgentState]]


def _extract_option(pattern: re.Pattern[str], content: str) -> str | None:
    match = pattern.search(content)
    return match.group(1) if match else None


def create_get_event_node(gateway_client: EventGatewayClient | None) -> GetEventNode:
    """Create a reusable node that retrieves Kubernetes events for a cluster."""

    async def get_event_node(state: AgentState) -> AgentState:
        cluster = _extract_option(_CLUSTER_PATTERN, state.msg)
        if cluster is None:
            state.msg = "请在 /get_event 中提供 cluster=<集群名称>。"
            return state
        if gateway_client is None:
            state.msg = "事件查询依赖未配置，暂时无法获取 Kubernetes 事件。"
            return state

        namespace = _extract_option(_NAMESPACE_PATTERN, state.msg)
        try:
            state.event_results = await gateway_client.get_events(cluster, namespace=namespace)
        except MCPGatewayClientError as exc:
            logger.warning("get_event_failed", cluster=cluster, error=str(exc))
            state.msg = f"事件查询失败：{exc}"
            return state
        state.msg = (
            "Kubernetes 事件查询结果：\n```json\n"
            + json.dumps(state.event_results, ensure_ascii=False, indent=2)
            + "\n```"
        )
        return state

    return get_event_node
