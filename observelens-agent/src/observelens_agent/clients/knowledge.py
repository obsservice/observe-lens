from typing import Any

import httpx


class KnowledgeClientError(Exception):
    """Raised when the knowledge retrieval service cannot provide context."""


class KnowledgeClient:
    def __init__(
        self,
        base_url: str | None,
        timeout_seconds: float,
        tenant_id: int,
        user_id: int,
        top_k: int,
    ) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))
        self._tenant_id = tenant_id
        self._user_id = user_id
        self._top_k = top_k

    async def retrieve_architecture(
        self, query: str, entity_type: str | None, entity_name: str | None
    ) -> list[dict[str, Any]]:
        if self._base_url is None:
            raise KnowledgeClientError("未配置知识库地址")
        payload: dict[str, object] = {"query": query, "top_k": self._top_k, "rerank": True}
        if entity_type and entity_name:
            payload["filters"] = {"entities": [{"type": entity_type, "name": entity_name}]}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/v1/knowledge/retrieval/search",
                    headers={
                        "X-Tenant-Id": str(self._tenant_id),
                        "X-User-Id": str(self._user_id),
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KnowledgeClientError("知识库检索服务不可用") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise KnowledgeClientError("知识库返回了无效检索数据") from exc
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            raise KnowledgeClientError("知识库返回了无效检索数据")
        return [item for item in body["results"] if isinstance(item, dict)]
