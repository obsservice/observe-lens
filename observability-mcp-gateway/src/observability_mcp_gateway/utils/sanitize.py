"""Query and input sanitisation helpers.

Provides basic guards against high-cardinality queries and injection risks.
Design doc §2.9 (security) and §10.3 (limits).
"""

from __future__ import annotations

import re

# Patterns that indicate potentially dangerous or high-cardinality queries.
_HIGH_CARDINALITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bup\b\s*(?:\{|$)", re.IGNORECASE),  # bare 'up' metric without filter
]


def check_promql_safety(query: str, *, require_label: bool = False) -> list[str]:
    """Return a list of safety warnings for a PromQL query.

    Args:
        query: The PromQL expression to check.
        require_label: If ``True``, warn when no label selector is present.
    """
    warnings: list[str] = []
    for pattern in _HIGH_CARDINALITY_PATTERNS:
        if pattern.search(query):
            warnings.append("Query may hit high cardinality (bare metric without label filter).")
    if require_label and "{" not in query:
        warnings.append("Query lacks a label selector — results may be unbounded.")
    return warnings


def check_logql_safety(query: str) -> list[str]:
    """Return a list of safety warnings for a LogQL query."""
    warnings: list[str] = []
    if not query.strip():
        warnings.append("Empty LogQL query.")
    return warnings


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate *text* to *max_chars*, appending an ellipsis if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "...[truncated]"
