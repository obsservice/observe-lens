"""Entry point for MCP Inspector (``mcp dev``).

Usage::

    mcp dev src/observability_mcp_gateway/inspector_entry.py

This module boots the gateway (logging, tool registration) and exposes the
FastMCP server instance as ``mcp`` so that ``mcp dev`` can discover it.
"""

from __future__ import annotations

from observability_mcp_gateway.mcp.server import create_mcp_server
from observability_mcp_gateway.mcp.tools import register_all_tools
from observability_mcp_gateway.observability import configure_logging

configure_logging()
register_all_tools()

mcp = create_mcp_server()
