"""Result normalisation service.

Transforms raw upstream responses into the unified :class:`ToolResult` format
suitable for LLM consumption.  Design doc §6.4 and §10.
"""

from __future__ import annotations

from typing import Any

from observability_mcp_gateway.config import LimitsConfig
from observability_mcp_gateway.mcp.schemas.common import Evidence, TimeRange, ToolResult


class NormalizeService:
    """Normalises raw adapter output into LLM-friendly :class:`ToolResult`."""

    def __init__(self, limits: LimitsConfig | None = None) -> None:
        self._limits = limits or LimitsConfig()

    # ── Prometheus ────────────────────────────────────────────

    def normalize_prometheus_query(
        self,
        raw: dict[str, Any],
        *,
        query: str,
        source: str = "prometheus",
    ) -> dict[str, Any]:
        """Normalise a Prometheus instant query result."""
        result_data = raw.get("data", {}).get("result", [])
        evidence: list[Evidence] = []
        for item in result_data[:10]:
            labels = item.get("metric", {})
            value = item.get("value", ["", ""])[1] if item.get("value") else ""
            evidence.append(
                Evidence(
                    title=labels.get("__name__", query),
                    value=str(value),
                    tags=labels,
                )
            )
        return ToolResult(
            summary=f"Prometheus query '{query}' returned {len(result_data)} series.",
            source=source,
            evidence=evidence,
            data={"result": result_data[:20]},
        ).model_dump()

    def normalize_prometheus_range(
        self,
        raw: dict[str, Any],
        *,
        query: str,
        time_range: TimeRange,
        source: str = "prometheus",
    ) -> dict[str, Any]:
        """Normalise a Prometheus range query result with statistics."""
        result_data = raw.get("data", {}).get("result", [])
        evidence: list[Evidence] = []
        for item in result_data[:10]:
            values = item.get("values", [])
            if not values:
                continue
            numeric_values = [float(v[1]) for v in values if v[1] not in ("NaN", "Inf", "-Inf")]
            if numeric_values:
                evidence.append(
                    Evidence(
                        title=item.get("metric", {}).get("__name__", query),
                        value=f"min={min(numeric_values):.4f} max={max(numeric_values):.4f} "
                        f"avg={sum(numeric_values) / len(numeric_values):.4f} "
                        f"last={numeric_values[-1]:.4f}",
                        tags=item.get("metric", {}),
                    )
                )
        return ToolResult(
            summary=f"Range query '{query}' returned {len(result_data)} series over "
            f"{time_range.start} → {time_range.end}.",
            source=source,
            time_range=time_range,
            evidence=evidence,
            data={"series_count": len(result_data)},
        ).model_dump()

    # ── Loki ──────────────────────────────────────────────────

    def normalize_loki_logs(
        self,
        raw: dict[str, Any],
        *,
        time_range: TimeRange,
        limit: int | None = None,
        source: str = "loki",
    ) -> dict[str, Any]:
        """Normalise a Loki log query result."""
        result_data = raw.get("data", {}).get("result", [])
        max_lines = limit or self._limits.max_log_lines
        total_lines = 0
        evidence: list[Evidence] = []
        for stream in result_data:
            labels = stream.get("stream", {})
            values = stream.get("values", [])
            for _ts, line in values:
                if total_lines >= max_lines:
                    break
                evidence.append(
                    Evidence(
                        title=f"[{labels.get('level', '?')}] {labels.get('job', '?')}",
                        value=line[:500],
                        tags=labels,
                    )
                )
                total_lines += 1
            if total_lines >= max_lines:
                break
        return ToolResult(
            summary=f"Log query returned {total_lines} lines (capped at {max_lines}).",
            source=source,
            time_range=time_range,
            evidence=evidence,
            data={"total_streams": len(result_data), "total_lines": total_lines},
        ).model_dump()

    # ── Jaeger ────────────────────────────────────────────────

    def normalize_trace(
        self,
        raw: dict[str, Any],
        *,
        trace_id: str,
        source: str = "jaeger",
    ) -> dict[str, Any]:
        """Normalise a Jaeger trace result, extracting key spans."""
        traces = raw.get("data", [])
        if not traces:
            return ToolResult(
                summary=f"Trace '{trace_id}' not found.",
                source=source,
            ).model_dump()

        trace = traces[0]
        spans = trace.get("spans", [])
        max_spans = self._limits.max_trace_spans
        error_spans = [s for s in spans if any(t.get("key") == "error" for t in s.get("tags", []))]
        key_spans = (error_spans + spans)[:max_spans]

        evidence: list[Evidence] = []
        for span in key_spans:
            evidence.append(
                Evidence(
                    title=f"{span.get('operationName', 'unknown')}",
                    value=f"duration={span.get('duration', 0)}μs",
                    tags={"spanID": span.get("spanID", ""), "service": span.get("processID", "")},
                )
            )
        return ToolResult(
            summary=f"Trace '{trace_id}' has {len(spans)} spans, {len(error_spans)} errors.",
            source=source,
            evidence=evidence,
            data={"span_count": len(spans), "error_count": len(error_spans)},
            next_actions=(
                ["loki_query_logs: Query logs for error span services"] if error_spans else []
            ),
        ).model_dump()

    # ── Kubernetes ────────────────────────────────────────────

    def normalize_k8s_workload(
        self,
        raw: dict[str, Any],
        *,
        workload_type: str,
        workload_name: str,
        source: str = "kubernetes",
    ) -> dict[str, Any]:
        """Normalise a Kubernetes workload status result."""
        status = raw.get("status", {})
        spec = raw.get("spec", {})
        evidence: list[Evidence] = []

        if workload_type in ("deployment", "statefulset"):
            replicas = spec.get("replicas", 0)
            ready = status.get("readyReplicas", 0)
            evidence.append(
                Evidence(
                    title="Replicas",
                    value=f"desired={replicas} ready={ready}",
                )
            )
        elif workload_type == "pod":
            phase = status.get("phase", "Unknown")
            restart_count = sum(
                cs.get("restartCount", 0) for cs in status.get("containerStatuses", [])
            )
            evidence.append(
                Evidence(title="Pod Status", value=f"phase={phase} restarts={restart_count}")
            )

        return ToolResult(
            summary=f"{workload_type}/{workload_name} status retrieved.",
            source=source,
            evidence=evidence,
            data={"status": status, "spec": spec},
        ).model_dump()

    # ── CMDB ──────────────────────────────────────────────────

    def normalize_entity(
        self,
        raw: dict[str, Any],
        *,
        source: str = "cmdb",
    ) -> dict[str, Any]:
        """Normalise an entity resolution result."""
        entity = raw.get("data", raw)
        evidence: list[Evidence] = []
        if isinstance(entity, dict):
            evidence.append(
                Evidence(
                    title=str(entity.get("name") or entity.get("id") or "entity"),
                    value=str(entity.get("type", "")),
                    tags=entity.get("labels", {}),
                )
            )
        return ToolResult(
            summary=f"Resolved entity: "
            f"{entity.get('name', '') if isinstance(entity, dict) else ''}",
            source=source,
            evidence=evidence,
            data=self._entity_data(raw, entity),
        ).model_dump()

    def _entity_data(self, raw: dict[str, Any], entity: Any) -> dict[str, Any]:
        """Extract a clean data dict for entity normalisation."""
        if not isinstance(raw, dict):
            return raw
        return {k: v for k, v in raw.items() if k != "data"} | {"entity": entity}

    # ── generic ───────────────────────────────────────────────

    def normalize_generic(
        self,
        raw: dict[str, Any],
        *,
        summary: str,
        source: str,
        time_range: TimeRange | None = None,
    ) -> dict[str, Any]:
        """Fallback normaliser for unstructured upstream results."""
        return ToolResult(
            summary=summary,
            source=source,
            time_range=time_range,
            data=raw,
        ).model_dump()
