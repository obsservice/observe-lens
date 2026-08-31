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

    async def get_metric_sets(self, entity_id: str) -> list[dict[str, Any]]:
        return await self.get_datasets(entity_id, dataset_type="metric")

    async def get_datasets(self, entity_id: str, dataset_type: str = "all") -> list[dict[str, Any]]:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self._datasets_url(entity_id, dataset_type))
                if response.status_code == 404:
                    raise CatalogClientError("未找到指定实体或其关联 Dataset")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise CatalogClientError("Observability Data Catalog 不可用") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise CatalogClientError(
                "Observability Data Catalog 返回了无效 MetricSet 数据"
            ) from exc
        return self._unwrap_metric_sets_response(payload)

    async def get_topology(self, entity_id: str, depth: int = 3) -> dict[str, Any]:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self._topology_url(entity_id, depth))
                if response.status_code == 404:
                    raise CatalogClientError("未找到指定实体拓扑")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise CatalogClientError("Observability Data Catalog 不可用") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise CatalogClientError("Observability Data Catalog 返回了无效拓扑数据") from exc
        return self._unwrap_mapping_response(payload, "拓扑")

    async def search_entities(self, keyword: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._entities_search_url(),
                    json={"keyword": keyword, "page": 0, "limit": limit},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise CatalogClientError("Observability Data Catalog 不可用") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise CatalogClientError("Observability Data Catalog 返回了无效实体搜索数据") from exc
        if not isinstance(payload, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体搜索数据")
        data = payload.get("data", payload)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体搜索数据")
        return [item for item in data["items"] if isinstance(item, dict)]

    def _entity_url(self, entity_id: str) -> str:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        return (
            f"{self._base_url}/api/v1/workspaces/{quote(self._workspace_id, safe='')}/"
            f"entities/{quote(entity_id, safe='')}"
        )

    def _metric_sets_url(self, entity_id: str) -> str:
        return self._datasets_url(entity_id, "metric")

    def _datasets_url(self, entity_id: str, dataset_type: str) -> str:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        return (
            f"{self._base_url}/api/v1/workspaces/{quote(self._workspace_id, safe='')}/"
            f"entities/{quote(entity_id, safe='')}/dataset?type={quote(dataset_type, safe='')}"
        )

    def _topology_url(self, entity_id: str, depth: int) -> str:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        return (
            f"{self._base_url}/api/v1/workspaces/{quote(self._workspace_id, safe='')}/"
            f"entities/{quote(entity_id, safe='')}/topology?depth={depth}"
        )

    def _entities_search_url(self) -> str:
        if self._base_url is None:
            raise CatalogClientError("未配置 Observability Data Catalog 地址")
        return (
            f"{self._base_url}/api/v1/workspaces/{quote(self._workspace_id, safe='')}/"
            "entities/search"
        )

    @staticmethod
    def _unwrap_entity_response(payload: object) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体数据")
        entity = payload.get("data", payload)
        if not isinstance(entity, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效实体数据")
        return cast(dict[str, Any], entity)

    @staticmethod
    def _unwrap_mapping_response(payload: object, resource_name: str) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CatalogClientError(f"Observability Data Catalog 返回了无效{resource_name}数据")
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise CatalogClientError(f"Observability Data Catalog 返回了无效{resource_name}数据")
        return cast(dict[str, Any], data)

    @staticmethod
    def _unwrap_metric_sets_response(payload: object) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            raise CatalogClientError("Observability Data Catalog 返回了无效 MetricSet 数据")
        data = payload.get("data", payload)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise CatalogClientError("Observability Data Catalog 返回了无效 MetricSet 数据")
        return [item for item in data["items"] if isinstance(item, dict)]
