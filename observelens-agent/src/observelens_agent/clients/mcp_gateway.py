from typing import Any, cast


class MCPGatewayClientError(Exception):
    """Raised when the observability MCP Gateway cannot execute a query."""


class MCPGatewayClient:
    def __init__(self, sse_url: str, timeout_seconds: float) -> None:
        self._sse_url = sse_url
        self._timeout_seconds = timeout_seconds

    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]:
        return await self._call_tool(
            "prom_range_query",
            {"query": query, "time_range": {"start": start, "end": end}, "step": step},
            "Observability MCP Gateway 指标查询失败",
        )

    async def query_logs(
        self, query: str, start: str, end: str, limit: int = 200
    ) -> dict[str, Any]:
        return await self._call_tool(
            "loki_query_logs",
            {"query": query, "time_range": {"start": start, "end": end}, "limit": limit},
            "Observability MCP Gateway 日志查询失败",
        )

    async def get_trace(self, trace_id: str) -> dict[str, Any]:
        return await self._call_tool(
            "trace_get_by_id",
            {"trace_id": trace_id},
            "Observability MCP Gateway 链路追踪查询失败",
        )

    async def get_events(
        self,
        cluster: str,
        namespace: str | None = None,
        field_selector: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        arguments: dict[str, object] = {"cluster": cluster, "limit": limit}
        if namespace:
            arguments["namespace"] = namespace
        if field_selector:
            arguments["field_selector"] = field_selector
        return await self._call_tool(
            "k8s_get_events",
            arguments,
            "Observability MCP Gateway 事件查询失败",
        )

    async def _call_tool(
        self, tool_name: str, arguments: dict[str, object], error_message: str
    ) -> dict[str, Any]:
        try:
            from fastmcp import Client
            from fastmcp.client import SSETransport

            client = Client(SSETransport(self._sse_url))
            async with client:
                result = await client.call_tool(
                    tool_name,
                    arguments,
                    timeout=self._timeout_seconds,
                )
        except Exception as exc:
            raise MCPGatewayClientError(error_message) from exc

        if not isinstance(result.data, dict):
            raise MCPGatewayClientError("Observability MCP Gateway 返回了无效指标数据")
        return cast(dict[str, Any], result.data)
