from starlette.requests import Request

from observelens_service.clients.reverse_proxy import ReverseProxyClient
from observelens_service.main import create_app


def test_reverse_proxy_builds_target_url_with_full_gateway_path() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/knowledge/retrieval/search",
            "query_string": b"top_k=6",
            "headers": [],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )
    client = ReverseProxyClient("http://localhost:3085/", 10)

    assert (
        client._build_target_url(request)
        == "http://localhost:3085/api/v1/knowledge/retrieval/search?top_k=6"
    )


def test_reverse_proxy_filters_hop_by_hop_headers() -> None:
    headers = ReverseProxyClient._forward_headers(
        {
            "host": "localhost:3081",
            "connection": "keep-alive",
            "x-tenant-id": "1",
            "x-user-id": "2",
        }
    )

    assert headers == {"x-tenant-id": "1", "x-user-id": "2"}


def test_runtime_openapi_shows_single_knowledge_proxy_placeholder() -> None:
    schema = create_app().openapi()
    knowledge_path = schema["paths"]["/api/v1/knowledge/{path}"]

    assert knowledge_path["x-observelens-proxy"] is True
    assert knowledge_path["x-observelens-upstream-service"] == "observelens-knowledge-base"
    assert knowledge_path["x-observelens-supported-methods"] == [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
    ]
    assert {"get"} == {"get", "post", "put", "patch", "delete", "options", "head"}.intersection(
        knowledge_path
    )
