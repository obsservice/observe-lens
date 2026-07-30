"""Session authentication and context extraction.

Extracts identity (tenant_id, user_id, roles) from the MCP session token
and populates :class:`SessionContext`.  The actual JWT validation will be
implemented in v0.2; v0.1 supports a passthrough mode for development.
Design doc §12 and §21.3.
"""

from __future__ import annotations

from typing import Any

import structlog

from observability_mcp_gateway.config import Settings, get_settings
from observability_mcp_gateway.context import SessionContext

logger = structlog.get_logger(__name__)


class SessionAuthenticator:
    """Authenticates MCP sessions and produces :class:`SessionContext`."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def authenticate(self, token: str | None) -> SessionContext:
        """Validate *token* and return the session context.

        When auth is disabled (development mode), a default context is returned.
        """
        if not self._settings.auth.enabled:
            logger.debug("auth_disabled_passthrough")
            return SessionContext(tenant_id="default", user_id="dev", roles=frozenset({"admin"}))

        if not token:
            raise ValueError("Authentication token required but not provided.")

        # TODO v0.2: implement JWT validation using jwt_issuer / jwt_audience.
        # For now, extract claims from the token header payload.
        claims = self._decode_claims(token)
        return SessionContext(
            tenant_id=claims.get("tenant_id", "default"),
            user_id=claims.get("user_id", "unknown"),
            roles=frozenset(claims.get("roles", [])),
        )

    def _decode_claims(self, token: str) -> dict[str, Any]:
        """Placeholder JWT claim extraction.

        v0.2 will replace this with proper JWT verification using
        ``PyJWT`` or ``python-jose``.
        """
        # Split JWT and decode payload — NOT verified, development only.
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format.")
        import base64
        import json

        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return dict(json.loads(payload_bytes))
