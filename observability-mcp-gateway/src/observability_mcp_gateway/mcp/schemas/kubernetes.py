"""Input / output schemas for Kubernetes tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from observability_mcp_gateway.mcp.schemas.common import TimeRange, ToolResult


class K8sGetWorkloadStatusInput(BaseModel):
    """Input for ``k8s_get_workload_status``."""

    cluster: str = Field(..., description="Cluster name.")
    namespace: str = Field(..., description="Namespace.")
    workload_type: str = Field(
        ..., description="Workload kind: 'deployment', 'statefulset', or 'pod'."
    )
    workload_name: str = Field(..., description="Workload name.")


class K8sGetEventsInput(BaseModel):
    """Input for ``k8s_get_events``."""

    cluster: str = Field(..., description="Cluster name.")
    namespace: str | None = Field(default=None, description="Namespace filter.")
    field_selector: str | None = Field(
        default=None, description="Kubernetes field selector expression."
    )
    time_range: TimeRange | None = Field(default=None, description="Event time window.")
    limit: int = Field(default=50, ge=1, le=500, description="Max events to return.")


class K8sGetResourceUsageInput(BaseModel):
    """Input for ``k8s_get_resource_usage``."""

    cluster: str = Field(..., description="Cluster name.")
    namespace: str = Field(..., description="Namespace.")
    workload_type: str = Field(..., description="Workload kind.")
    workload_name: str = Field(..., description="Workload name.")
    time_range: TimeRange = Field(..., description="Usage time window.")


K8sGetWorkloadStatusOutput = ToolResult
K8sGetEventsOutput = ToolResult
K8sGetResourceUsageOutput = ToolResult
