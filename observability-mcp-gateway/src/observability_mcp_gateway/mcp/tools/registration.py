"""Tool registration — wires tool definitions into the registry at startup.

Each tool is registered with its name, description, input/output schema, and
async handler.  The handler delegates to :class:`QueryService` for execution.
Design doc §6.1, §7, §8, §15.3.
"""

from __future__ import annotations

from typing import Any

from observability_mcp_gateway.core.registry import ToolDefinition, registry
from observability_mcp_gateway.mcp.schemas import (
    EntityResolveInput,
    EntityResolveOutput,
    K8sGetWorkloadStatusInput,
    K8sGetWorkloadStatusOutput,
    LokiQueryLogsInput,
    LokiQueryLogsOutput,
    PromQueryInput,
    PromQueryOutput,
    PromRangeQueryInput,
    PromRangeQueryOutput,
    TraceGetByIdInput,
    TraceGetByIdOutput,
)
from observability_mcp_gateway.services.query_service import QueryService

_query_service = QueryService()


async def _prom_query(request: Any) -> dict[str, Any]:
    return await _query_service.prom_query(request)


async def _prom_range_query(request: Any) -> dict[str, Any]:
    return await _query_service.prom_range_query(request)


async def _loki_query_logs(request: Any) -> dict[str, Any]:
    return await _query_service.loki_query_logs(request)


async def _trace_get_by_id(request: Any) -> dict[str, Any]:
    return await _query_service.trace_get_by_id(request)


async def _k8s_get_workload_status(request: Any) -> dict[str, Any]:
    return await _query_service.k8s_get_workload_status(request)


async def _entity_resolve(request: Any) -> dict[str, Any]:
    return await _query_service.entity_resolve(request)


def register_all_tools() -> None:
    """Register all v0.1 tools into the global registry."""
    tools: list[ToolDefinition] = [
        ToolDefinition(
            name="prom_query",
            description="Execute a Prometheus instant query (PromQL).",
            input_schema=PromQueryInput,
            output_schema=PromQueryOutput,
            handler=_prom_query,
        ),
        ToolDefinition(
            name="prom_range_query",
            description="Execute a Prometheus range query with time window and step.",
            input_schema=PromRangeQueryInput,
            output_schema=PromRangeQueryOutput,
            handler=_prom_range_query,
        ),
        ToolDefinition(
            name="loki_query_logs",
            description="Query logs from Loki using LogQL within a time range.",
            input_schema=LokiQueryLogsInput,
            output_schema=LokiQueryLogsOutput,
            handler=_loki_query_logs,
        ),
        ToolDefinition(
            name="trace_get_by_id",
            description="Retrieve a full Jaeger trace by its trace ID.",
            input_schema=TraceGetByIdInput,
            output_schema=TraceGetByIdOutput,
            handler=_trace_get_by_id,
        ),
        ToolDefinition(
            name="k8s_get_workload_status",
            description="Get Kubernetes workload (Deployment/StatefulSet/Pod) status.",
            input_schema=K8sGetWorkloadStatusInput,
            output_schema=K8sGetWorkloadStatusOutput,
            handler=_k8s_get_workload_status,
        ),
        ToolDefinition(
            name="entity_resolve",
            description="Resolve a service name, IP, pod, or alias to a unified entity.",
            input_schema=EntityResolveInput,
            output_schema=EntityResolveOutput,
            handler=_entity_resolve,
        ),
    ]

    for tool in tools:
        registry.register(tool)
