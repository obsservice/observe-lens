"""Prometheus source adapter.

Abstracts the Prometheus HTTP API behind the uniform adapter interface.
Design doc §6.3 and §8.1.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.core.base_adapter import BaseAdapter
from observability_mcp_gateway.core.errors import ToolError

logger = structlog.get_logger(__name__)


class PrometheusAdapter(BaseAdapter):
    """Adapter for the Prometheus HTTP query API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "prometheus"

    @property
    def _base_url(self) -> str:
        return self._settings.prometheus_base_url

    @property
    def _timeout(self) -> float:
        return self._settings.prometheus_timeout_seconds

    async def health_check(self) -> bool:
        """Return ``True`` if Prometheus ``/-/healthy`` responds 200."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/-/healthy")
                return resp.status_code == 200
        except Exception:
            logger.warning("prometheus_health_check_failed", upstream=self._base_url)
            return False

    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute an instant query (``/api/v1/query``)."""
        params: dict[str, Any] = {"query": request["query"]}
        if request.get("timestamp"):
            params["time"] = request["timestamp"]
        return await self._get("/api/v1/query", params)

    async def range_query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a range query (``/api/v1/query_range``)."""
        params = {
            "query": request["query"],
            "start": request["start"],
            "end": request["end"],
            "step": request.get("step", "30s"),
        }
        return await self._get("/api/v1/query_range", params)

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return dict(resp.json())
        except httpx.TimeoutException as exc:
            raise ToolError.timeout(self.name) from exc
        except httpx.HTTPStatusError as exc:
            raise ToolError.invalid_query(
                f"Prometheus returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolError.upstream_unavailable(self.name, str(exc)) from exc
