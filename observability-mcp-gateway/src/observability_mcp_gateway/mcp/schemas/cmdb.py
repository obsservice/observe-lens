"""Input / output schemas for CMDB / entity tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from observability_mcp_gateway.mcp.schemas.common import ToolResult


class EntityResolveInput(BaseModel):
    """Input for ``entity_resolve``."""

    identifier: str = Field(
        ..., description="Service name, alias, IP, pod name, namespace, or topic to resolve."
    )
    identifier_type: str | None = Field(
        default=None,
        description="Hint for identifier type: 'service', 'ip', 'pod', 'namespace', 'topic'.",
    )


class EntityTopologyInput(BaseModel):
    """Input for ``entity_topology``."""

    entity_id: str = Field(..., description="Resolved entity ID.")
    depth: int = Field(default=2, ge=1, le=5, description="Topology traversal depth.")


class EntityOwnersInput(BaseModel):
    """Input for ``entity_owners``."""

    entity_id: str = Field(..., description="Resolved entity ID.")


EntityResolveOutput = ToolResult
EntityTopologyOutput = ToolResult
EntityOwnersOutput = ToolResult
