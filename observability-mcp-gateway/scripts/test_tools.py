"""Local MCP tool testing script.

Connects to a running MCP Gateway server via SSE and calls each tool.

Prerequisites::

    # 1. Start the gateway server
    make run

    # 2. Run this script (in another terminal)
    ./.venv/bin/python scripts/test_tools.py

If the gateway runs on a different host/port, pass it as the first argument::

    ./.venv/bin/python scripts/test_tools.py http://localhost:3084/sse
"""

from __future__ import annotations

import asyncio
import json
import sys

from fastmcp import Client


def _print_result(result: object) -> None:
    """Pretty-print a tool call result."""
    if hasattr(result, "structured_content") and result.structured_content:
        print(json.dumps(result.structured_content, indent=2, ensure_ascii=False))
    elif hasattr(result, "data") and result.data:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    else:
        print(str(result))


async def main(server_url: str) -> None:
    print(f"连接 MCP Gateway: {server_url}\n")

    async with Client(server_url) as client:
        # 1. List all tools
        tools = await client.list_tools()
        print("=" * 60)
        print("工具列表")
        print("=" * 60)
        for t in tools:
            print(f"  {t.name}: {t.description}")

        # 2. Call entity_resolve
        print("\n" + "=" * 60)
        print("调用 entity_resolve")
        print("=" * 60)
        result = await client.call_tool("entity_resolve", {"identifier": "test-service"})
        _print_result(result)

        # 3. Call prom_query
        print("\n" + "=" * 60)
        print("调用 prom_query")
        print("=" * 60)
        result = await client.call_tool("prom_query", {"query": "up"})
        _print_result(result)

        # 4. Call k8s_get_workload_status
        print("\n" + "=" * 60)
        print("调用 k8s_get_workload_status")
        print("=" * 60)
        result = await client.call_tool(
            "k8s_get_workload_status",
            {
                "cluster": "test-cluster",
                "namespace": "default",
                "workload_type": "deployment",
                "workload_name": "nginx",
            },
        )
        _print_result(result)

        # 5. Call trace_get_by_id
        print("\n" + "=" * 60)
        print("调用 trace_get_by_id")
        print("=" * 60)
        result = await client.call_tool("trace_get_by_id", {"trace_id": "abc123"})
        _print_result(result)

        # 6. Call loki_query_logs
        print("\n" + "=" * 60)
        print("调用 loki_query_logs")
        print("=" * 60)
        result = await client.call_tool(
            "loki_query_logs",
            {
                "query": '{job="test"} |= "error"',
                "time_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-01T01:00:00Z",
                },
                "limit": 10,
            },
        )
        _print_result(result)

        print("\n" + "=" * 60)
        print("全部工具调用完成")
        print("=" * 60)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3084/sse"
    asyncio.run(main(url))
