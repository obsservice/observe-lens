"""Application configuration via Pydantic Settings.

All configuration is injected through environment variables with the prefix
``OBSERVABILITY_MCP_GATEWAY_``.  See ``.env.example`` for available options.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UpstreamConfig(BaseModel):
    """Connection settings for a single external observability system."""

    base_url: str = ""
    timeout_ms: int = 5000


class LimitsConfig(BaseModel):
    """Guard-rails to prevent context explosion for the LLM consumer."""

    max_tool_output_chars: int = 20_000
    max_log_lines: int = 200
    max_trace_spans: int = 100
    request_timeout_ms: int = 10_000


class AuthConfig(BaseModel):
    """Authentication configuration."""

    enabled: bool = False
    jwt_issuer: str = ""
    jwt_audience: str = ""


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
    auth: AuthConfig = AuthConfig()

    # ── upstream systems ─────────────────────────────────────
    prometheus: UpstreamConfig = UpstreamConfig(base_url="http://localhost:9090")
    loki: UpstreamConfig = UpstreamConfig(base_url="http://localhost:3100")
    jaeger: UpstreamConfig = UpstreamConfig(base_url="http://localhost:16686")
    kubernetes: UpstreamConfig = UpstreamConfig()
    cmdb: UpstreamConfig = UpstreamConfig()

    # ── limits ───────────────────────────────────────────────
    limits: LimitsConfig = LimitsConfig()


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
