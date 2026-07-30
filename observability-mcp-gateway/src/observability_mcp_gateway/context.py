"""Session and request context for MCP tool execution.

Identity information (``tenant_id``, ``user_id``, ``roles``) is injected from
the authenticated session, **not** from tool call arguments.  See the design
doc §21.3 for the rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SessionContext:
    """Identity context established during MCP session handshake.

    Populated by the auth layer from the JWT / internal token and made
    available to every tool invocation via :class:`RequestContext`.
    """

    tenant_id: str
    user_id: str
    roles: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Per-request context propagated through the tool execution pipeline."""

    session: SessionContext
    request_id: str
    tool_name: str
