"""CMDB / entity source adapter.

Abstracts entity resolution, topology, and ownership queries against the
ObserveLens Observability Catalog service.  This adapter calls the Catalog
HTTP API — it does **not** access MySQL, ClickHouse, or Neo4j directly
(per ``Agent.md`` storage constraints).

Design doc §6.3 and §8.5.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.core.base_adapter import BaseAdapter
from observability_mcp_gateway.core.errors import ToolError

logger = structlog.get_logger(__name__)


class CMDBAdapter(BaseAdapter):
    """Adapter for the Observability Catalog HTTP API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "cmdb"

    @property
    def _base_url(self) -> str:
        return self._settings.cmdb_base_url

    @property
    def _timeout(self) -> float:
        return self._settings.cmdb_timeout_seconds

    async def health_check(self) -> bool:
        """Return ``True`` if the Catalog service health endpoint responds 200."""
        if not self._base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/health")
                return resp.status_code == 200
        except Exception:
            logger.warning("cmdb_health_check_failed", upstream=self._base_url)
            return False

    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Resolve an identifier to a unified entity."""
        params: dict[str, str] = {"identifier": request["identifier"]}
        if request.get("identifier_type"):
            params["type"] = request["identifier_type"]
        return await self._get("/api/v1/entities/resolve", params)

    async def get_topology(self, request: dict[str, Any]) -> dict[str, Any]:
        """Retrieve entity relationship topology."""
        entity_id = request["entity_id"]
        depth = request.get("depth", 2)
        return await self._get(
            f"/api/v1/entities/{entity_id}/topology",
            {"depth": str(depth)},
        )

    async def get_owners(self, request: dict[str, Any]) -> dict[str, Any]:
        """Retrieve entity owners, team, and on-call info."""
        entity_id = request["entity_id"]
        return await self._get(f"/api/v1/entities/{entity_id}/owners")

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
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
                f"Catalog API returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolError.upstream_unavailable(self.name, str(exc)) from exc
