from collections.abc import Mapping

import httpx
from fastapi import Request
from fastapi.responses import Response

from observelens_service.common.exceptions import DependencyUnavailableError

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

RESPONSE_HEADERS_MANAGED_BY_GATEWAY = {
    "date",
    "server",
}


class ReverseProxyClient:
    def __init__(
        self,
        upstream_base_url: str | None,
        timeout_seconds: float,
        service_name: str = "Upstream service",
    ) -> None:
        self._upstream_base_url = upstream_base_url.rstrip("/") if upstream_base_url else None
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))
        self._service_name = service_name

    async def proxy(self, request: Request, *, strip_path_prefix: str = "") -> Response:
        if self._upstream_base_url is None:
            raise DependencyUnavailableError(self._service_name)

        target_url = self._build_target_url(request, strip_path_prefix)
        headers = self._forward_headers(request.headers)
        body = await request.body()

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                upstream_response = await client.request(
                    request.method,
                    target_url,
                    content=body,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError(self._service_name) from exc

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=self._response_headers(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type"),
        )

    def _build_target_url(self, request: Request, strip_path_prefix: str = "") -> str:
        path = request.url.path
        if strip_path_prefix:
            if path == strip_path_prefix:
                path = "/"
            elif path.startswith(f"{strip_path_prefix}/"):
                path = path[len(strip_path_prefix) :]
        query = request.url.query
        target_url = f"{self._upstream_base_url}{path}"
        if query:
            target_url = f"{target_url}?{query}"
        return target_url

    @staticmethod
    def _forward_headers(headers: Mapping[str, str]) -> dict[str, str]:
        return {
            name: value
            for name, value in headers.items()
            if name.lower() not in HOP_BY_HOP_HEADERS
            and name.lower() not in RESPONSE_HEADERS_MANAGED_BY_GATEWAY
        }

    @staticmethod
    def _response_headers(headers: Mapping[str, str]) -> dict[str, str]:
        return {
            name: value for name, value in headers.items() if name.lower() not in HOP_BY_HOP_HEADERS
        }
