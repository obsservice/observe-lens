"""Input / output schemas for Jaeger / trace tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from observability_mcp_gateway.mcp.schemas.common import TimeRange, ToolResult


class TraceGetByIdInput(BaseModel):
    """Input for ``trace_get_by_id``."""

    trace_id: str = Field(..., description="Jaeger trace ID.")


class TraceSearchInput(BaseModel):
    """Input for ``trace_search``."""

    service: str | None = Field(default=None, description="Service name filter.")
    operation: str | None = Field(default=None, description="Operation name filter.")
    time_range: TimeRange = Field(..., description="Query time window.")
    min_duration: str | None = Field(default=None, description="Minimum duration (e.g. '500ms').")
    max_duration: str | None = Field(default=None, description="Maximum duration (e.g. '10s').")
    tags: dict[str, str] = Field(default_factory=dict, description="Tag key-value filters.")
    limit: int = Field(default=20, ge=1, le=100, description="Max traces to return.")


TraceGetByIdOutput = ToolResult
TraceSearchOutput = ToolResult
