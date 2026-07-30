"""Base helpers for tool handler implementations.

Tool handlers follow the three-layer pattern (design doc §15.3):
  - Handler: receives validated input, delegates to service.
  - Service: orchestrates adapter calls and normalisation.
  - Adapter: executes the external HTTP request.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseToolHandler(ABC):
    """Base class for MCP tool handlers.

    Subclasses implement :meth:`execute`, which receives the validated input
    model and returns a raw dict to be validated against the tool's output
    schema by the server.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name matching the registered definition."""

    @abstractmethod
    async def execute(self, request: BaseModel) -> dict[str, Any]:
        """Execute the tool logic and return a raw result dict."""
