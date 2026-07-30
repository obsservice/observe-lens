"""Integration tests for tool registration and server creation."""

from __future__ import annotations

from observability_mcp_gateway.core.registry import registry
from observability_mcp_gateway.mcp.tools import register_all_tools


def test_register_all_tools() -> None:
    registry.clear()
    register_all_tools()
    names = registry.list_names()
    assert "prom_query" in names
    assert "prom_range_query" in names
    assert "loki_query_logs" in names
    assert "trace_get_by_id" in names
    assert "k8s_get_workload_status" in names
    assert "entity_resolve" in names


def test_all_tools_have_schemas() -> None:
    registry.clear()
    register_all_tools()
    for name in registry.list_names():
        tool = registry.get(name)
        assert tool is not None
        assert tool.input_schema is not None
        assert tool.output_schema is not None
        assert tool.description
        assert tool.handler is not None


def test_tool_count() -> None:
    registry.clear()
    register_all_tools()
    assert len(registry.list_names()) == 6
