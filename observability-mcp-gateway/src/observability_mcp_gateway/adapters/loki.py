"""Loki source adapter.

Abstracts the Loki HTTP API for log querying and pattern search.
Design doc §6.3 and §8.2.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.core.base_adapter import BaseAdapter
from observability_mcp_gateway.core.errors import ToolError

logger = structlog.get_logger(__name__)


class LokiAdapter(BaseAdapter):
    """Adapter for the Loki log aggregation API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "loki"

    @property
    def _base_url(self) -> str:
        return self._settings.loki_base_url

    @property
    def _timeout(self) -> float:
        return self._settings.loki_timeout_seconds

    async def health_check(self) -> bool:
        """Return ``True`` if Loki ``/ready`` responds 200."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/ready")
                return resp.status_code == 200
        except Exception:
            logger.warning("loki_health_check_failed", upstream=self._base_url)
            return False

    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a Loki log query (``/loki/api/v1/query_range``)."""
        params = {
            "query": request["query"],
            "start": request["start"],
            "end": request["end"],
            "limit": request.get("limit", 200),
        }
        return await self._get("/loki/api/v1/query_range", params)

    async def search_patterns(self, request: dict[str, Any]) -> dict[str, Any]:
        """Search for keyword / error patterns via Loki query syntax."""
        regex = "|".join(request["patterns"])
        query = f'{{job=~".+"}} |=~ "{regex}"'
        params = {
            "query": query,
            "start": request["start"],
            "end": request["end"],
            "limit": request.get("limit", 200),
        }
        return await self._get("/loki/api/v1/query_range", params)

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
                f"Loki returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolError.upstream_unavailable(self.name, str(exc)) from exc
