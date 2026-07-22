# mypy: disable-error-code=arg-type

from collections.abc import Mapping, Sequence
from typing import cast

import httpx

from observelens_service.common.exceptions import DependencyUnavailableError, ResourceNotFoundError

QueryValue = str | int | float | bool | None | Sequence[str | int | float | bool | None]


class KnowledgeBaseClient:
    def __init__(self, base_url: str | None, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def list_files(self, params: Mapping[str, QueryValue]) -> dict[str, object]:
        return cast(dict[str, object], await self._request("GET", "/api/v1/files", params=params))

    async def get_file(self, file_id: str) -> dict[str, object]:
        return cast(dict[str, object], await self._request("GET", f"/api/v1/files/{file_id}"))

    async def delete_file(self, file_id: str) -> None:
        await self._request("DELETE", f"/api/v1/files/{file_id}")

    async def get_status(self, file_id: str) -> dict[str, object]:
        return cast(
            dict[str, object], await self._request("GET", f"/api/v1/files/{file_id}/status")
        )

    async def reindex(self, file_id: str) -> dict[str, object]:
        return cast(
            dict[str, object], await self._request("POST", f"/api/v1/files/{file_id}/reindex")
        )

    async def upload(self, file_name: str, content_type: str, content: bytes) -> dict[str, object]:
        files = {"file": (file_name, content, content_type)}
        return cast(dict[str, object], await self._request("POST", "/api/v1/files", files=files))

    async def file_types(self) -> list[dict[str, str]]:
        return self._items(await self._request("GET", "/api/v1/file-types"))

    async def index_statuses(self) -> list[dict[str, str]]:
        return self._items(await self._request("GET", "/api/v1/index-statuses"))

    async def _request(self, method: str, path: str, **kwargs: object) -> object:
        if self._base_url is None:
            raise DependencyUnavailableError("Knowledge Base")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, f"{self._base_url}{path}", **kwargs)
                if response.status_code == 404:
                    raise ResourceNotFoundError("Knowledge file")
                response.raise_for_status()
                if response.status_code == 204:
                    return {}
                return cast(object, response.json())
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError("Knowledge Base") from exc

    @staticmethod
    def _items(response: object) -> list[dict[str, str]]:
        items = response.get("items", response) if isinstance(response, dict) else response
        return cast(list[dict[str, str]], items)
