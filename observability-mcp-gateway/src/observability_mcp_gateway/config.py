"""Application configuration via Pydantic Settings.

All configuration is injected through environment variables with the prefix
``OBSERVABILITY_MCP_GATEWAY_``.  See ``.env.example`` for available options.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level gateway settings loaded from environment / ``.env`` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVABILITY_MCP_GATEWAY_",
        extra="ignore",
    )

    # ── server ────────────────────────────────────────────────
    mode: Literal["stdio", "sse"] = "sse"
    host: str = "0.0.0.0"
    port: int = 3084
    environment: str = "development"
    log_level: str = "INFO"

    # ── auth ──────────────────────────────────────────────────
    auth_enabled: bool = False
    auth_jwt_issuer: str = ""
    auth_jwt_audience: str = ""

    # ── upstream: prometheus ─────────────────────────────────
    prometheus_base_url: str = "http://localhost:9090"
    prometheus_timeout_ms: int = 5000

    # ── upstream: loki ───────────────────────────────────────
    loki_base_url: str = "http://localhost:3100"
    loki_timeout_ms: int = 5000

    # ── upstream: jaeger ─────────────────────────────────────
    jaeger_base_url: str = "http://localhost:16686"
    jaeger_timeout_ms: int = 5000

    # ── upstream: kubernetes ─────────────────────────────────
    kubernetes_base_url: str = ""
    kubernetes_timeout_ms: int = 5000

    # ── upstream: cmdb ───────────────────────────────────────
    cmdb_base_url: str = ""
    cmdb_timeout_ms: int = 5000

    # ── limits ───────────────────────────────────────────────
    max_tool_output_chars: int = 20_000
    max_log_lines: int = 200
    max_trace_spans: int = 100
    request_timeout_ms: int = 10_000

    @property
    def prometheus_timeout_seconds(self) -> float:
        return self.prometheus_timeout_ms / 1000.0

    @property
    def loki_timeout_seconds(self) -> float:
        return self.loki_timeout_ms / 1000.0

    @property
    def jaeger_timeout_seconds(self) -> float:
        return self.jaeger_timeout_ms / 1000.0

    @property
    def kubernetes_timeout_seconds(self) -> float:
        return self.kubernetes_timeout_ms / 1000.0

    @property
    def cmdb_timeout_seconds(self) -> float:
        return self.cmdb_timeout_ms / 1000.0


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
