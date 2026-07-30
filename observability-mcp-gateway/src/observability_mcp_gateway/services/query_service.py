"""Query orchestration service.

Coordinates adapter calls, retry logic, and result normalisation.
Design doc §6.4, §9, and §15.3.
"""

from __future__ import annotations

from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from observability_mcp_gateway.adapters import (
    CMDBAdapter,
    JaegerAdapter,
    KubernetesAdapter,
    LokiAdapter,
    PrometheusAdapter,
)
from observability_mcp_gateway.core.errors import ToolError
from observability_mcp_gateway.services.normalize_service import NormalizeService

logger = structlog.get_logger(__name__)


class QueryService:
    """Orchestrates adapter calls with retry and normalisation."""

    def __init__(self, normalize: NormalizeService | None = None) -> None:
        self._prometheus = PrometheusAdapter()
        self._loki = LokiAdapter()
        self._jaeger = JaegerAdapter()
        self._kubernetes = KubernetesAdapter()
        self._cmdb = CMDBAdapter()
        self._normalize = normalize or NormalizeService()

    # ── Prometheus ────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def prom_query(self, request: Any) -> dict[str, Any]:
        query = request.query
        raw = await self._prometheus.query({"query": query, "timestamp": request.timestamp})
        return self._normalize.normalize_prometheus_query(raw, query=query)

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def prom_range_query(self, request: Any) -> dict[str, Any]:
        raw = await self._prometheus.range_query(
            {
                "query": request.query,
                "start": request.time_range.start,
                "end": request.time_range.end,
                "step": request.step,
            }
        )
        return self._normalize.normalize_prometheus_range(
            raw, query=request.query, time_range=request.time_range
        )

    # ── Loki ──────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def loki_query_logs(self, request: Any) -> dict[str, Any]:
        raw = await self._loki.query(
            {
                "query": request.query,
                "start": request.time_range.start,
                "end": request.time_range.end,
                "limit": request.limit,
            }
        )
        return self._normalize.normalize_loki_logs(
            raw, time_range=request.time_range, limit=request.limit
        )

    # ── Jaeger ────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def trace_get_by_id(self, request: Any) -> dict[str, Any]:
        raw = await self._jaeger.query({"trace_id": request.trace_id})
        return self._normalize.normalize_trace(raw, trace_id=request.trace_id)

    # ── Kubernetes ────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def k8s_get_workload_status(self, request: Any) -> dict[str, Any]:
        raw = await self._kubernetes.query(
            {
                "workload_type": request.workload_type,
                "namespace": request.namespace,
                "workload_name": request.workload_name,
            }
        )
        return self._normalize.normalize_k8s_workload(
            raw, workload_type=request.workload_type, workload_name=request.workload_name
        )

    # ── CMDB ──────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ToolError),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    async def entity_resolve(self, request: Any) -> dict[str, Any]:
        raw = await self._cmdb.query(
            {"identifier": request.identifier, "identifier_type": request.identifier_type}
        )
        return self._normalize.normalize_entity(raw)

    # ── health ────────────────────────────────────────────────

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks for all upstream adapters."""
        import asyncio

        results = await asyncio.gather(
            self._prometheus.health_check(),
            self._loki.health_check(),
            self._jaeger.health_check(),
            self._kubernetes.health_check(),
            self._cmdb.health_check(),
            return_exceptions=True,
        )
        names = ["prometheus", "loki", "jaeger", "kubernetes", "cmdb"]
        return {name: (isinstance(r, bool) and r) for name, r in zip(names, results, strict=True)}
