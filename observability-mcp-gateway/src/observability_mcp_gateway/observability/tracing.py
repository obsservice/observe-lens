"""Tracing configuration using OpenTelemetry.

Sets up W3C Trace Context propagation so that spans from the Agent side
and the Gateway side can be correlated.  Design doc §14.3 and §21.8.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TracingConfig:
    """Tracing configuration holder.

    v0.1 provides a no-op tracer.  v0.2+ should integrate with
    ``opentelemetry-sdk`` and configure an OTLP exporter.
    """

    def __init__(self, service_name: str = "observability-mcp-gateway") -> None:
        self.service_name = service_name
        self._enabled = False

    def configure(self, endpoint: str | None = None) -> None:
        """Initialise OpenTelemetry tracing.

        Args:
            endpoint: OTLP collector endpoint.  If ``None``, tracing is disabled.
        """
        if not endpoint:
            logger.info("tracing_disabled", service=self.service_name)
            return

        # Placeholder for actual OTel SDK setup — will be filled in v0.2.
        self._enabled = True
        logger.info("tracing_configured", service=self.service_name, endpoint=endpoint)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_trace_context(self) -> dict[str, Any]:
        """Return the current trace context for logging correlation."""
        return {"service": self.service_name, "enabled": self._enabled}


# Module-level singleton.
tracer = TracingConfig()
