"""Jaeger source adapter.

Abstracts the Jaeger query API for trace retrieval and search.
Design doc §6.3 and §8.3.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.core.base_adapter import BaseAdapter
from observability_mcp_gateway.core.errors import ToolError

logger = structlog.get_logger(__name__)


class JaegerAdapter(BaseAdapter):
    """Adapter for the Jaeger query API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._upstream = self._settings.jaeger

    @property
    def name(self) -> str:
        return "jaeger"

    async def health_check(self) -> bool:
        """Return ``True`` if Jaeger API is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._upstream.base_url}/api/services")
                return resp.status_code == 200
        except Exception:
            logger.warning("jaeger_health_check_failed", upstream=self._upstream.base_url)
            return False

    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Get a trace by ID (``/api/traces/{trace_id}``)."""
        trace_id = request["trace_id"]
        return await self._get(f"/api/traces/{trace_id}")

    async def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """Search traces (``/api/traces``) with service / operation / tag filters."""
        params: dict[str, Any] = {}
        if request.get("service"):
            params["service"] = request["service"]
        if request.get("operation"):
            params["operation"] = request["operation"]
        if request.get("min_duration"):
            params["minDuration"] = request["min_duration"]
        if request.get("max_duration"):
            params["maxDuration"] = request["max_duration"]
        if request.get("start"):
            params["start"] = request["start"]
        if request.get("end"):
            params["end"] = request["end"]
        if request.get("limit"):
            params["limit"] = request["limit"]
        for key, value in request.get("tags", {}).items():
            params[f"tags[{key}]"] = value
        return await self._get("/api/traces", params)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._upstream.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return dict(resp.json())
        except httpx.TimeoutException as exc:
            raise ToolError.timeout(self.name) from exc
        except httpx.HTTPStatusError as exc:
            raise ToolError.invalid_query(f"Jaeger returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ToolError.upstream_unavailable(self.name, str(exc)) from exc

    @property
    def _timeout(self) -> float:
        return self._upstream.timeout_ms / 1000.0
