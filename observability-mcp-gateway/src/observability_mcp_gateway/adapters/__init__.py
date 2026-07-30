"""Source adapters that abstract external observability system APIs."""

from observability_mcp_gateway.adapters.cmdb import CMDBAdapter
from observability_mcp_gateway.adapters.jaeger import JaegerAdapter
from observability_mcp_gateway.adapters.kubernetes import KubernetesAdapter
from observability_mcp_gateway.adapters.loki import LokiAdapter
from observability_mcp_gateway.adapters.prometheus import PrometheusAdapter

__all__ = [
    "CMDBAdapter",
    "JaegerAdapter",
    "KubernetesAdapter",
    "LokiAdapter",
    "PrometheusAdapter",
]
