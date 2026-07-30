"""Cache service for short-lived result caching.

Suitable for CMDB entity mappings, resource topology, and high-frequency
repeated queries.  Real-time metrics, fault logs, and traces should not be
cached for long.  Design doc §13.1.
"""

from __future__ import annotations

import time
from typing import Any


class CacheService:
    """Simple in-memory TTL cache (v0.1).

    v0.2+ should replace this with a Redis-backed implementation for
    multi-instance deployments.
    """

    def __init__(self, default_ttl_seconds: int = 60) -> None:
        self._default_ttl = default_ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        """Return cached value if not expired, else ``None``."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store *value* under *key* with the given TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        """Remove a single cache entry."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all cache entries."""
        self._store.clear()
