"""Time and timestamp utility helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_rfc3339(ts: str) -> datetime:
    """Parse an RFC 3339 timestamp string into a timezone-aware ``datetime``."""
    return datetime.fromisoformat(ts)


def to_unix_seconds(ts: str) -> float:
    """Convert an RFC 3339 timestamp to Unix epoch seconds."""
    dt = parse_rfc3339(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.timestamp()


def now_rfc3339() -> str:
    """Return the current UTC time as an RFC 3339 string."""
    return datetime.now(UTC).isoformat()
