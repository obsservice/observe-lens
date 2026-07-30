"""Unit tests for structured tool errors."""

from __future__ import annotations

from observability_mcp_gateway.core.errors import ErrorCode, ToolError


def test_timeout_is_retryable() -> None:
    err = ToolError.timeout("prometheus")
    assert err.code == ErrorCode.TIMEOUT
    assert err.retryable is True
    assert err.upstream == "prometheus"


def test_auth_failed_is_not_retryable() -> None:
    err = ToolError(ErrorCode.AUTH_FAILED, "no permissions")
    assert err.retryable is False


def test_invalid_query_is_not_retryable() -> None:
    err = ToolError.invalid_query("bad syntax")
    assert err.code == ErrorCode.INVALID_QUERY
    assert err.retryable is False


def test_upstream_unavailable_is_retryable() -> None:
    err = ToolError.upstream_unavailable("loki")
    assert err.code == ErrorCode.UPSTREAM_UNAVAILABLE
    assert err.retryable is True


def test_to_dict() -> None:
    err = ToolError(
        ErrorCode.TIMEOUT,
        "timed out",
        upstream="jaeger",
        next_actions=["retry with smaller time range"],
    )
    d = err.to_dict()
    assert d["code"] == "TIMEOUT"
    assert d["upstream"] == "jaeger"
    assert d["retryable"] is True
    assert "retry with smaller time range" in d["next_actions"]  # type: ignore[arg-type]


def test_internal_error() -> None:
    err = ToolError.internal("something broke")
    assert err.code == ErrorCode.INTERNAL_ERROR
    assert err.retryable is False
