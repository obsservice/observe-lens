from typing import Any, cast
from urllib.parse import quote

import httpx


class CatalogClientError(Exception):
    """Raised when the Observability Data Catalog cannot serve an entity request."""


class CatalogClient:
    def __init__(self, base_url: str | None, timeout_seconds: float, workspace_id: str) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))
        self._workspace_id = workspace_id

    async def get_entity(self, entity_id: str) -> dict[str, Any]:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self._entity_url(entity_id))
                if response.status_code == 404:
                    raise CatalogClientError("未找到指定实体")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise CatalogClientError("Observability Data Catalog 不可用") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise CatalogClientError("Observability Data Catalog 返回了无效实体数据") from exc
        return self._unwrap_entity_response(payload)

    def _entity_url(self, entity_id: str) -> str:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        return (
            f"{self._base_url}/api/v1/workspaces/{quote(self._workspace_id, safe='')}/"
            f"entities/{quote(entity_id, safe='')}"
        )

    @staticmethod
    def _unwrap_entity_response(payload: object) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体数据")
        entity = payload.get("data", payload)
        if not isinstance(entity, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体数据")
        return cast(dict[str, Any], entity)
