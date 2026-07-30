"""Unit tests for the normalize service."""

from __future__ import annotations

from observability_mcp_gateway.mcp.schemas.common import TimeRange
from observability_mcp_gateway.services.normalize_service import NormalizeService


def test_normalize_prometheus_query() -> None:
    svc = NormalizeService()
    raw = {
        "data": {
            "result": [
                {"metric": {"__name__": "up", "job": "prometheus"}, "value": [1700000000, "1"]},
            ]
        }
    }
    result = svc.normalize_prometheus_query(raw, query="up")
    assert result["source"] == "prometheus"
    assert result["summary"]  # non-empty
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["title"] == "up"


def test_normalize_prometheus_range() -> None:
    svc = NormalizeService()
    raw = {
        "data": {
            "result": [
                {
                    "metric": {"__name__": "cpu_usage"},
                    "values": [[1700000000, "0.5"], [1700000010, "0.8"]],
                }
            ]
        }
    }
    result = svc.normalize_prometheus_range(
        raw,
        query="cpu_usage",
        time_range=TimeRange(start="2023-11-14T22:00:00Z", end="2023-11-14T22:10:00Z"),
    )
    assert result["source"] == "prometheus"
    assert "min=" in result["evidence"][0]["value"]
    assert "max=" in result["evidence"][0]["value"]


def test_normalize_loki_logs() -> None:
    svc = NormalizeService()
    raw = {
        "data": {
            "result": [
                {
                    "stream": {"level": "error", "job": "api"},
                    "values": [["1700000000", "connection refused"]],
                }
            ]
        }
    }
    result = svc.normalize_loki_logs(
        raw,
        time_range=TimeRange(start="2023-11-14T22:00:00Z", end="2023-11-14T22:10:00Z"),
    )
    assert result["source"] == "loki"
    assert result["evidence"][0]["value"] == "connection refused"


def test_normalize_trace_not_found() -> None:
    svc = NormalizeService()
    result = svc.normalize_trace({"data": []}, trace_id="abc123")
    assert "not found" in result["summary"].lower()


def test_normalize_trace_with_errors() -> None:
    svc = NormalizeService()
    raw = {
        "data": [
            {
                "spans": [
                    {
                        "spanID": "s1",
                        "operationName": "GET /api",
                        "duration": 50000,
                        "processID": "p1",
                        "tags": [{"key": "error", "value": True}],
                    }
                ]
            }
        ]
    }
    result = svc.normalize_trace(raw, trace_id="abc123")
    assert result["data"]["error_count"] == 1
    assert len(result["next_actions"]) > 0
