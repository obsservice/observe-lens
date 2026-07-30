"""Input / output schemas for Prometheus tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from observability_mcp_gateway.mcp.schemas.common import Scope, TimeRange, ToolResult


class PromQueryInput(BaseModel):
    """Input for ``prom_query`` (instant query)."""

    query: str = Field(..., description="PromQL expression.")
    timestamp: str | None = Field(default=None, description="Evaluation timestamp (RFC 3339).")
    scope: Scope | None = Field(default=None, description="Resource scope filter.")


class PromRangeQueryInput(BaseModel):
    """Input for ``prom_range_query``."""

    query: str = Field(..., description="PromQL expression.")
    time_range: TimeRange = Field(..., description="Query time window.")
    step: str = Field(default="30s", description="Resolution step (e.g. '30s', '1m').")
    scope: Scope | None = Field(default=None, description="Resource scope filter.")


class PromTopkInput(BaseModel):
    """Input for ``prom_topk_metrics``."""

    query: str = Field(..., description="PromQL expression returning a vector.")
    time_range: TimeRange = Field(..., description="Query time window.")
    topk: int = Field(default=10, ge=1, le=100, description="Number of top items to return.")
    step: str = Field(default="30s", description="Resolution step.")


# Output reuses the unified ToolResult model.
PromQueryOutput = ToolResult
PromRangeQueryOutput = ToolResult
PromTopkOutput = ToolResult
