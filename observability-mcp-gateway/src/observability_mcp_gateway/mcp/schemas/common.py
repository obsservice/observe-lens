"""Common input / output schemas shared across MCP tools.

Design doc §10 — unified input constraints and output model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ── common input fields ──────────────────────────────────────


class TimeRange(BaseModel):
    """A bounded time window for time-series, log, or trace queries."""

    start: str = Field(..., description="Start timestamp in RFC 3339 format.")
    end: str = Field(..., description="End timestamp in RFC 3339 format.")


class Scope(BaseModel):
    """Resource scope to restrict a query (cluster / namespace / service)."""

    cluster: str | None = Field(default=None, description="Cluster name.")
    namespace: str | None = Field(default=None, description="Kubernetes namespace.")
    service: str | None = Field(default=None, description="Service name.")


# ── unified output model ─────────────────────────────────────


class Evidence(BaseModel):
    """A single piece of evidence extracted from a tool result."""

    title: str = Field(..., description="Short label for the evidence.")
    value: str = Field(..., description="Value or summary of the evidence.")
    tags: dict[str, str] = Field(default_factory=dict, description="Contextual tags.")


class ToolResult(BaseModel):
    """Unified output model returned by every MCP tool (§10.2)."""

    summary: str = Field(..., description="Short conclusion of the result.")
    source: str = Field(..., description="Originating system (e.g. 'prometheus').")
    time_range: TimeRange | None = Field(default=None, description="Query time window.")
    evidence: list[Evidence] = Field(default_factory=list, description="Key evidence items.")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured payload.")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested follow-up actions."
    )
