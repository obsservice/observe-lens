"""Audit service for recording tool invocations.

Records who called what tool, with what parameters, what was returned,
and how long it took.  Sensitive parameters are masked.  Design doc §6.5.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {"token", "password", "secret", "api_key", "authorization", "cookie", "access_key"}
)


def _mask_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *data* with sensitive values replaced by ``"***"``."""
    masked: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive(value)
        else:
            masked[key] = value
    return masked


@dataclass(slots=True)
class AuditEntry:
    """A single audit log entry for a tool invocation."""

    tool_name: str
    tenant_id: str
    user_id: str
    request_id: str
    arguments: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    result_size: int = 0
    cache_hit: bool = False
    error_code: str = ""
    status: str = "success"
    timestamp: float = field(default_factory=time.time)


class AuditService:
    """Records structured audit entries for every tool call."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        """Log and store an audit entry."""
        masked = _mask_sensitive(entry.arguments)
        log_entry = AuditEntry(**{**asdict(entry), "arguments": masked})
        self._entries.append(log_entry)
        logger.info(
            "tool_audit",
            tool_name=log_entry.tool_name,
            tenant_id=log_entry.tenant_id,
            user_id=log_entry.user_id,
            request_id=log_entry.request_id,
            duration_ms=log_entry.duration_ms,
            result_size=log_entry.result_size,
            cache_hit=log_entry.cache_hit,
            error_code=log_entry.error_code,
            status=log_entry.status,
        )

    def get_entries(
        self,
        *,
        tool_name: str | None = None,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Return recent audit entries, optionally filtered."""
        entries = self._entries
        if tool_name:
            entries = [e for e in entries if e.tool_name == tool_name]
        if tenant_id:
            entries = [e for e in entries if e.tenant_id == tenant_id]
        return list(reversed(entries[-limit:]))

    def clear(self) -> None:
        """Remove all stored audit entries."""
        self._entries.clear()
