"""Input / output schemas for Loki tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from observability_mcp_gateway.mcp.schemas.common import TimeRange, ToolResult


class LokiQueryLogsInput(BaseModel):
    """Input for ``loki_query_logs``."""

    query: str = Field(..., description="LogQL expression.")
    time_range: TimeRange = Field(..., description="Query time window.")
    limit: int = Field(default=200, ge=1, le=5000, description="Max log lines to return.")


class LokiSearchPatternsInput(BaseModel):
    """Input for ``loki_search_patterns``."""

    patterns: list[str] = Field(..., description="Keywords, error codes, or exception names.")
    time_range: TimeRange = Field(..., description="Query time window.")
    limit: int = Field(default=200, ge=1, le=5000, description="Max results to return.")


LokiQueryLogsOutput = ToolResult
LokiSearchPatternsOutput = ToolResult
