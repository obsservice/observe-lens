"""Metrics definitions for gateway self-observability.

Defines the core metrics listed in design doc §14.1.  The actual Prometheus
exposition endpoint is exposed via the Admin HTTP API (§19).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class Counter:
    """Simple monotonically increasing counter."""

    value: int = 0

    def inc(self, amount: int = 1) -> None:
        self.value += amount


@dataclass(slots=True)
class Histogram:
    """Simple histogram for latency tracking."""

    count: int = 0
    total_seconds: float = 0.0
    _buckets: list[float] = field(
        default_factory=lambda: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
    _bucket_counts: list[int] = field(default_factory=lambda: [0] * 9)

    def observe(self, seconds: float) -> None:
        self.count += 1
        self.total_seconds += seconds
        for i, bound in enumerate(self._buckets):
            if seconds <= bound:
                self._bucket_counts[i] += 1
                break

    @property
    def avg(self) -> float:
        return self.total_seconds / self.count if self.count > 0 else 0.0


class MetricsRegistry:
    """In-memory metrics registry (v0.1).

    v0.2+ should integrate with ``prometheus_client`` or OpenTelemetry
    metrics for proper exposition format and multi-instance aggregation.
    """

    def __init__(self) -> None:
        self.mcp_requests_total: Counter = Counter()
        self.mcp_tool_calls_total: Counter = Counter()
        self.mcp_tool_failures_total: Counter = Counter()
        self.upstream_timeout_total: Counter = Counter()
        self.audit_events_total: Counter = Counter()
        self.mcp_request_duration: Histogram = Histogram()
        self.upstream_latency: Histogram = Histogram()

    def snapshot(self) -> dict[str, Any]:
        """Return a dict snapshot of all metrics for the Admin API."""
        return {
            "mcp_requests_total": self.mcp_requests_total.value,
            "mcp_tool_calls_total": self.mcp_tool_calls_total.value,
            "mcp_tool_failures_total": self.mcp_tool_failures_total.value,
            "upstream_timeout_total": self.upstream_timeout_total.value,
            "audit_events_total": self.audit_events_total.value,
            "mcp_request_duration": {
                "count": self.mcp_request_duration.count,
                "avg_seconds": round(self.mcp_request_duration.avg, 6),
            },
            "upstream_latency": {
                "count": self.upstream_latency.count,
                "avg_seconds": round(self.upstream_latency.avg, 6),
            },
        }


# Module-level singleton.
metrics = MetricsRegistry()
