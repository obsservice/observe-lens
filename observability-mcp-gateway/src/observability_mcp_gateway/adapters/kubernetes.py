"""Kubernetes source adapter.

Abstracts the Kubernetes API for workload status, events, and resource usage.
Design doc §6.3 and §8.4.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.core.base_adapter import BaseAdapter
from observability_mcp_gateway.core.errors import ToolError

logger = structlog.get_logger(__name__)

_WORKLOAD_PATH: dict[str, str] = {
    "deployment": "/apis/apps/v1/namespaces/{ns}/deployments/{name}",
    "statefulset": "/apis/apps/v1/namespaces/{ns}/statefulsets/{name}",
    "pod": "/api/v1/namespaces/{ns}/pods/{name}",
}


class KubernetesAdapter(BaseAdapter):
    """Adapter for the Kubernetes API server."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        token: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._token = token

    @property
    def name(self) -> str:
        return "kubernetes"

    @property
    def _base_url(self) -> str:
        return self._settings.kubernetes_base_url

    @property
    def _timeout(self) -> float:
        return self._settings.kubernetes_timeout_seconds

    async def health_check(self) -> bool:
        """Return ``True`` if the Kubernetes API ``/healthz`` responds 200."""
        if not self._base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base_url}/healthz",
                    headers=self._headers(),
                )
                return resp.status_code == 200
        except Exception:
            logger.warning("kubernetes_health_check_failed", upstream=self._base_url)
            return False

    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get workload status (Deployment / StatefulSet / Pod)."""
        workload_type = request["workload_type"]
        path_template = _WORKLOAD_PATH.get(workload_type)
        if path_template is None:
            raise ToolError.invalid_query(f"Unknown workload type: {workload_type}")
        path = path_template.format(ns=request["namespace"], name=request["workload_name"])
        return await self._get(path)

    async def get_events(self, request: dict[str, Any]) -> dict[str, Any]:
        """List Kubernetes events for a namespace."""
        ns = request.get("namespace", "")
        path = f"/api/v1/namespaces/{ns}/events" if ns else "/api/v1/events"
        params: dict[str, str] = {}
        if request.get("field_selector"):
            params["fieldSelector"] = request["field_selector"]
        if request.get("limit"):
            params["limit"] = str(request["limit"])
        return await self._get(path, params)

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                return dict(resp.json())
        except httpx.TimeoutException as exc:
            raise ToolError.timeout(self.name) from exc
        except httpx.HTTPStatusError as exc:
            raise ToolError.invalid_query(
                f"Kubernetes API returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolError.upstream_unavailable(self.name, str(exc)) from exc

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
