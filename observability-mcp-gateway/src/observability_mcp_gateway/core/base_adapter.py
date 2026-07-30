"""Abstract base class for source adapters.

Each external observability system (Prometheus, Loki, Jaeger, K8s, CMDB)
implements this interface so the service layer can treat them uniformly.
Design doc §6.3 and §15.2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Uniform interface for all observability source adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this adapter (e.g. ``"prometheus"``)."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return ``True`` if the upstream system is reachable and healthy."""

    @abstractmethod
    async def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a query against the upstream system.

        Args:
            request: Adapter-specific query parameters.

        Returns:
            Raw (un-normalised) result from the upstream system.

        Raises:
            ToolError: On timeout, upstream failure, or invalid query.
        """
