"""Unit tests for the cache service."""

from __future__ import annotations

import time

from observability_mcp_gateway.core.cache import CacheService


def test_set_and_get() -> None:
    cache = CacheService(default_ttl_seconds=10)
    cache.set("key1", {"value": 42})
    assert cache.get("key1") == {"value": 42}


def test_get_missing_key() -> None:
    cache = CacheService()
    assert cache.get("nonexistent") is None


def test_ttl_expiration() -> None:
    cache = CacheService(default_ttl_seconds=1)
    cache.set("short_lived", "data", ttl_seconds=0)
    time.sleep(0.1)
    assert cache.get("short_lived") is None


def test_invalidate() -> None:
    cache = CacheService()
    cache.set("key", "value")
    cache.invalidate("key")
    assert cache.get("key") is None


def test_clear() -> None:
    cache = CacheService()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
