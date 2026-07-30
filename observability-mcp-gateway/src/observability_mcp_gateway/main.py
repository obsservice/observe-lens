"""Gateway entry point.

Reads configuration, initialises observability, registers tools, creates the
MCP server, and starts the service.  Design doc §15.1.
"""

from __future__ import annotations

import structlog

from observability_mcp_gateway.config import get_settings
from observability_mcp_gateway.mcp.server import create_mcp_server
from observability_mcp_gateway.mcp.tools import register_all_tools
from observability_mcp_gateway.observability import configure_logging, metrics, tracer

logger = structlog.get_logger(__name__)


def bootstrap() -> None:
    """Initialise logging, tracing, metrics, and tool registration."""
    settings = get_settings()

    configure_logging(log_level=settings.log_level)
    tracer.configure()
    metrics.mcp_requests_total.inc()

    register_all_tools()
    logger.info(
        "gateway_bootstrapped",
        environment=settings.environment,
        mode=settings.mode,
        tools=metrics.mcp_tool_calls_total.value,
    )


def main() -> None:
    """Create the MCP server and start it in the configured transport mode."""
    bootstrap()
    settings = get_settings()

    mcp = create_mcp_server()

    logger.info("mcp_server_starting", mode=settings.mode, host=settings.host, port=settings.port)

    if settings.mode == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
