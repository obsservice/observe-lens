"""Tool registry for managing MCP tool metadata and lifecycle.

Tools are registered at startup and can be toggled by environment, tenant, or
role.  Design doc §6.2.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(slots=True, frozen=True)
class ToolDefinition:
    """Metadata describing a single MCP tool.

    Attributes:
        name: Stable ``verb_noun`` tool identifier.
        description: Human-readable summary shown to the LLM.
        input_schema: Pydantic model class for input validation.
        output_schema: Pydantic model class for output validation.
        handler: Async callable that executes the tool logic.
        enabled: Whether the tool is currently visible to Agents.
    """

    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: ToolHandler
    enabled: bool = True


class ToolRegistry:
    """Central registry for all MCP tools exposed by the gateway."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register or replace a tool definition."""
        self._tools[definition.name] = definition

    def unregister(self, name: str) -> None:
        """Remove a tool by name.  No-op if not registered."""
        self._tools.pop(name, None)

    def get(self, name: str) -> ToolDefinition | None:
        """Return the tool definition for *name*, or ``None``."""
        return self._tools.get(name)

    def list_tools(self, *, include_disabled: bool = False) -> list[ToolDefinition]:
        """Return all registered tools, optionally including disabled ones."""
        if include_disabled:
            return list(self._tools.values())
        return [t for t in self._tools.values() if t.enabled]

    def list_names(self, *, include_disabled: bool = False) -> list[str]:
        """Return tool names in registration order."""
        return [t.name for t in self.list_tools(include_disabled=include_disabled)]

    def is_enabled(self, name: str) -> bool:
        """Return ``True`` if *name* is registered and enabled."""
        tool = self._tools.get(name)
        return tool is not None and tool.enabled

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Toggle a tool's visibility without removing it."""
        tool = self._tools.get(name)
        if tool is None:
            return
        self._tools[name] = ToolDefinition(
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            output_schema=tool.output_schema,
            handler=tool.handler,
            enabled=enabled,
        )

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()


# Module-level singleton used by the server and tool registration code.
registry = ToolRegistry()
