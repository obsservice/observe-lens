"""Pydantic schemas for MCP tool inputs and outputs."""

from observability_mcp_gateway.mcp.schemas.cmdb import (
    EntityOwnersInput,
    EntityOwnersOutput,
    EntityResolveInput,
    EntityResolveOutput,
    EntityTopologyInput,
    EntityTopologyOutput,
)
from observability_mcp_gateway.mcp.schemas.common import Evidence, Scope, TimeRange, ToolResult
from observability_mcp_gateway.mcp.schemas.jaeger import (
    TraceGetByIdInput,
    TraceGetByIdOutput,
    TraceSearchInput,
    TraceSearchOutput,
)
from observability_mcp_gateway.mcp.schemas.kubernetes import (
    K8sGetEventsInput,
    K8sGetEventsOutput,
    K8sGetResourceUsageInput,
    K8sGetResourceUsageOutput,
    K8sGetWorkloadStatusInput,
    K8sGetWorkloadStatusOutput,
)
from observability_mcp_gateway.mcp.schemas.loki import (
    LokiQueryLogsInput,
    LokiQueryLogsOutput,
    LokiSearchPatternsInput,
    LokiSearchPatternsOutput,
)
from observability_mcp_gateway.mcp.schemas.prometheus import (
    PromQueryInput,
    PromQueryOutput,
    PromRangeQueryInput,
    PromRangeQueryOutput,
    PromTopkInput,
    PromTopkOutput,
)

__all__ = [
    # common
    "Evidence",
    "Scope",
    "TimeRange",
    "ToolResult",
    # prometheus
    "PromQueryInput",
    "PromQueryOutput",
    "PromRangeQueryInput",
    "PromRangeQueryOutput",
    "PromTopkInput",
    "PromTopkOutput",
    # loki
    "LokiQueryLogsInput",
    "LokiQueryLogsOutput",
    "LokiSearchPatternsInput",
    "LokiSearchPatternsOutput",
    # jaeger
    "TraceGetByIdInput",
    "TraceGetByIdOutput",
    "TraceSearchInput",
    "TraceSearchOutput",
    # kubernetes
    "K8sGetWorkloadStatusInput",
    "K8sGetWorkloadStatusOutput",
    "K8sGetEventsInput",
    "K8sGetEventsOutput",
    "K8sGetResourceUsageInput",
    "K8sGetResourceUsageOutput",
    # cmdb
    "EntityResolveInput",
    "EntityResolveOutput",
    "EntityTopologyInput",
    "EntityTopologyOutput",
    "EntityOwnersInput",
    "EntityOwnersOutput",
]
