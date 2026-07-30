"""Unit tests for tool input/output schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from observability_mcp_gateway.mcp.schemas import (
    PromQueryInput,
    PromRangeQueryInput,
    TimeRange,
    ToolResult,
)


def test_prom_query_input_valid() -> None:
    inp = PromQueryInput(query="up")
    assert inp.query == "up"
    assert inp.timestamp is None


def test_prom_range_query_input_valid() -> None:
    inp = PromRangeQueryInput(
        query="rate(http_requests_total[5m])",
        time_range=TimeRange(start="2023-11-14T22:00:00Z", end="2023-11-14T22:10:00Z"),
    )
    assert inp.step == "30s"


def test_prom_range_query_input_missing_time_range() -> None:
    with pytest.raises(ValidationError):
        PromRangeQueryInput(query="up")  # type: ignore[call-arg]


def test_tool_result_minimal() -> None:
    result = ToolResult(summary="test", source="prometheus")
    assert result.summary == "test"
    assert result.source == "prometheus"
    assert result.evidence == []
    assert result.next_actions == []


def test_tool_result_full() -> None:
    result = ToolResult(
        summary="found issues",
        source="loki",
        time_range=TimeRange(start="2023-11-14T00:00:00Z", end="2023-11-14T01:00:00Z"),
        evidence=[{"title": "error", "value": "timeout", "tags": {"level": "error"}}],
        data={"count": 5},
        next_actions=["trace_get_by_id"],
    )
    dumped = result.model_dump()
    assert dumped["source"] == "loki"
    assert dumped["evidence"][0]["title"] == "error"
