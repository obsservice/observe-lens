from typing import Any, cast


class MCPGatewayClientError(Exception):
    """Raised when the observability MCP Gateway cannot execute a metric query."""


class MCPGatewayClient:
    def __init__(self, sse_url: str, timeout_seconds: float) -> None:
        self._sse_url = sse_url
        self._timeout_seconds = timeout_seconds

    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]:
        try:
            from fastmcp import Client
            from fastmcp.client import SSETransport

            client = Client(SSETransport(self._sse_url))
            async with client:
                result = await client.call_tool(
                    "prom_range_query",
                    {
                        "query": query,
                        "time_range": {"start": start, "end": end},
                        "step": step,
                    },
                    timeout=self._timeout_seconds,
                )
        except Exception as exc:
            raise MCPGatewayClientError("Observability MCP Gateway 指标查询失败") from exc

        if not isinstance(result.data, dict):
            raise MCPGatewayClientError("Observability MCP Gateway 返回了无效指标数据")
        return cast(dict[str, Any], result.data)
