"""Structured error model for MCP tool failures.

Every tool error is mapped to a stable error code (design doc §9.2) so the
Agent can make automated retry / degrade decisions (§21.6).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self


class ErrorCode(StrEnum):
    """Stable error codes returned to the Agent."""

    TIMEOUT = "TIMEOUT"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_QUERY = "INVALID_QUERY"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    PARTIAL_RESULT = "PARTIAL_RESULT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Error codes that the Agent may automatically retry.
_RETRYABLE_CODES: frozenset[ErrorCode] = frozenset(
    {ErrorCode.TIMEOUT, ErrorCode.UPSTREAM_UNAVAILABLE}
)


class ToolError(Exception):
    """Structured error returned by an MCP tool or adapter.

    Attributes:
        code: Stable error code for Agent-side decision logic.
        message: Human-readable summary.
        upstream: Name of the upstream system that failed, if applicable.
        retryable: Whether the Agent should retry the call.
        next_actions: Suggested follow-up actions.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        upstream: str = "",
        retryable: bool | None = None,
        next_actions: list[str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.upstream = upstream
        self.retryable = retryable if retryable is not None else code in _RETRYABLE_CODES
        self.next_actions = next_actions or []
        super().__init__(message)

    def to_dict(self) -> dict[str, object]:
        """Serialise to the structured error body consumed by the Agent."""
        return {
            "code": self.code.value,
            "message": self.message,
            "upstream": self.upstream,
            "retryable": self.retryable,
            "next_actions": self.next_actions,
        }

    @classmethod
    def timeout(cls, upstream: str, message: str = "") -> Self:
        return cls(ErrorCode.TIMEOUT, message or f"{upstream} request timed out", upstream=upstream)

    @classmethod
    def upstream_unavailable(cls, upstream: str, message: str = "") -> Self:
        return cls(
            ErrorCode.UPSTREAM_UNAVAILABLE,
            message or f"{upstream} is unavailable",
            upstream=upstream,
        )

    @classmethod
    def invalid_query(cls, message: str) -> Self:
        return cls(ErrorCode.INVALID_QUERY, message)

    @classmethod
    def internal(cls, message: str = "Internal error") -> Self:
        return cls(ErrorCode.INTERNAL_ERROR, message)
