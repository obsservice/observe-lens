from collections.abc import Mapping, Sequence
from typing import cast

import httpx

from observelens_service.common.exceptions import DependencyUnavailableError, ResourceNotFoundError


class CatalogClient:
    def __init__(self, base_url: str | None, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def search(
        self, query: str | None, entity_type: str | None, page: int, page_size: int
    ) -> dict[str, object]:
        return cast(
            dict[str, object],
            await self._get(
                "/api/v1/entities/search",
                {"query": query, "type": entity_type, "page": page, "page_size": page_size},
            ),
        )

    async def get(self, entity_id: str) -> dict[str, object]:
        return cast(dict[str, object], await self._get(f"/api/v1/entities/{entity_id}"))

    async def topology(self, entity_id: str, depth: int) -> dict[str, object]:
        return cast(
            dict[str, object],
            await self._get(f"/api/v1/entities/{entity_id}/topology", {"depth": depth}),
        )

    async def relations(self, entity_id: str) -> list[dict[str, object]]:
        response = await self._get(f"/api/v1/entities/{entity_id}/relations")
        items = response.get("items", response) if isinstance(response, dict) else response
        return cast(list[dict[str, object]], items)

    async def types(self) -> list[dict[str, str]]:
        response = await self._get("/api/v1/entities/types")
        items = response.get("items", response) if isinstance(response, dict) else response
        return cast(list[dict[str, str]], items)

    async def _get(
        self,
        path: str,
        params: Mapping[
            str, str | int | float | bool | None | Sequence[str | int | float | bool | None]
        ]
        | None = None,
    ) -> object:
        if self._base_url is None:
            raise DependencyUnavailableError("Observability Catalog")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}{path}", params=params)
                if response.status_code == 404:
                    raise ResourceNotFoundError("Entity")
                response.raise_for_status()
                return cast(object, response.json())
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError("Observability Catalog") from exc
