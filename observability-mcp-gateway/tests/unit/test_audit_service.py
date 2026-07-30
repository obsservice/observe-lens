"""Unit tests for the audit service."""

from __future__ import annotations

from observability_mcp_gateway.observability.audit import AuditEntry, AuditService


def test_record_and_retrieve() -> None:
    service = AuditService()
    service.record(
        AuditEntry(
            tool_name="prom_query",
            tenant_id="tenant-1",
            user_id="user-1",
            request_id="req-1",
            arguments={"query": "up"},
            duration_ms=42.0,
            result_size=1024,
        )
    )
    entries = service.get_entries()
    assert len(entries) == 1
    assert entries[0].tool_name == "prom_query"
    assert entries[0].duration_ms == 42.0


def test_sensitive_field_masking() -> None:
    service = AuditService()
    service.record(
        AuditEntry(
            tool_name="loki_query_logs",
            tenant_id="t1",
            user_id="u1",
            request_id="r1",
            arguments={"query": "error", "token": "secret-value", "password": "p4ss"},
        )
    )
    entries = service.get_entries()
    assert entries[0].arguments["token"] == "***"
    assert entries[0].arguments["password"] == "***"
    assert entries[0].arguments["query"] == "error"


def test_filter_by_tool_name() -> None:
    service = AuditService()
    for name in ("prom_query", "loki_query_logs", "prom_query"):
        service.record(
            AuditEntry(
                tool_name=name,
                tenant_id="t1",
                user_id="u1",
                request_id="r1",
            )
        )
    prom_entries = service.get_entries(tool_name="prom_query")
    assert len(prom_entries) == 2


def test_clear() -> None:
    service = AuditService()
    service.record(AuditEntry(tool_name="t", tenant_id="t", user_id="u", request_id="r"))
    service.clear()
    assert service.get_entries() == []
