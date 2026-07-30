"""Gateway self-observability: structured logging, metrics, tracing, and audit."""

from observability_mcp_gateway.observability.audit import AuditEntry, AuditService
from observability_mcp_gateway.observability.logging import configure_logging
from observability_mcp_gateway.observability.metrics import MetricsRegistry, metrics
from observability_mcp_gateway.observability.tracing import TracingConfig, tracer

__all__ = [
    "AuditEntry",
    "AuditService",
    "MetricsRegistry",
    "TracingConfig",
    "configure_logging",
    "metrics",
    "tracer",
]
