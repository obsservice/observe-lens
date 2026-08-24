from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from observelens_service.clients.reverse_proxy import ReverseProxyClient
from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context
from observelens_service.config.settings import get_settings

router = APIRouter(prefix="/catalog", tags=["Catalog"])


def get_proxy_client() -> ReverseProxyClient:
    settings = get_settings()
    catalog_base_url = (
        str(settings.catalog_base_url).rstrip("/") if settings.catalog_base_url else None
    )
    return ReverseProxyClient(
        f"{catalog_base_url}/api/v1" if catalog_base_url else None,
        settings.catalog_timeout_seconds,
        service_name="Observability Data Catalog",
    )


ProxyDependency = Annotated[ReverseProxyClient, Depends(get_proxy_client)]
ContextDependency = Annotated[RequestContext, Depends(get_request_context)]


@router.api_route(
    "",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def proxy_catalog_request(
    request: Request,
    context: ContextDependency,
    proxy_client: ProxyDependency,
    path: str = "",
) -> Response:
    _ = context
    _ = path
    return await proxy_client.proxy(request, strip_path_prefix="/api/v1/catalog")
