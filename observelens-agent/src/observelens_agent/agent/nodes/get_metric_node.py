import asyncio
import json
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import structlog

from observelens_agent.agent.nodes.get_info_node import extract_entity_id
from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.catalog import CatalogClientError
from observelens_agent.clients.mcp_gateway import MCPGatewayClientError

logger = structlog.get_logger(__name__)

_WINDOW_PATTERN = re.compile(r"(?:最近|last)\s*(\d+)\s*(m|min|分钟|h|小时|d|天)", re.IGNORECASE)
_METRIC_SYNONYMS: dict[str, tuple[str, ...]] = {
    "cpu": ("cpu", "处理器", "核", "算力"),
    "memory": ("memory", "内存", "mem"),
    "network_receive": ("receive", "接收", "入流量", "入站"),
    "network_transmit": ("transmit", "发送", "出流量", "出站"),
    "latency": ("latency", "延迟", "耗时", "p95", "p99"),
    "error": ("error", "错误", "失败", "异常", "错误率"),
    "qps": ("qps", "rps", "吞吐", "请求量", "流量"),
}
_LABEL_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "cluster": ("cluster",),
    "namespace": ("namespace",),
    "pod": ("pod", "id", "display_name"),
    "node": ("node", "node_name"),
    "ip": ("ip", "pod_ip"),
    "service": ("service", "service_name", "display_name", "id"),
}


class MetricCatalogClient(Protocol):
    async def get_entity(self, entity_id: str) -> dict[str, Any]: ...

    async def get_metric_sets(self, entity_id: str) -> list[dict[str, Any]]: ...


class MetricGatewayClient(Protocol):
    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class MetricDefinition:
    dataset_name: str
    description: str
    golden_metric: bool
    label_names: tuple[str, ...]
    name: str
    promql: str
    unit: str


GetMetricNode = Callable[[AgentState], Awaitable[AgentState]]


def extract_metric_definitions(dataset_items: Sequence[dict[str, Any]]) -> list[MetricDefinition]:
    definitions: list[MetricDefinition] = []
    for item in dataset_items:
        dataset = item.get("dataset")
        if not isinstance(dataset, dict):
            continue
        document = dataset.get("document", dataset)
        if not isinstance(document, dict) or document.get("kind") != "MetricSet":
            continue
        metadata = document.get("metadata")
        spec = document.get("spec")
        if not isinstance(metadata, dict) or not isinstance(spec, dict):
            continue
        dataset_name = metadata.get("name")
        if not isinstance(dataset_name, str):
            continue
        labels = spec.get("labels")
        static_keys = labels.get("static_keys") if isinstance(labels, dict) else None
        label_names = tuple(
            entry["name"]
            for entry in static_keys or []
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        )
        for metric in spec.get("metrics", []):
            if not isinstance(metric, dict):
                continue
            name = metric.get("name")
            promql = metric.get("generator")
            if not isinstance(name, str) or not isinstance(promql, str):
                continue
            definitions.append(
                MetricDefinition(
                    dataset_name=dataset_name,
                    description=str(metric.get("description", "")),
                    golden_metric=bool(metric.get("golden_metric", False)),
                    label_names=label_names,
                    name=name,
                    promql=promql.strip(),
                    unit=str(metric.get("unit", "")),
                )
            )
    return definitions


def select_metric_definitions(
    definitions: Sequence[MetricDefinition], content: str, limit: int
) -> list[MetricDefinition]:
    normalized_content = content.lower()

    def score(definition: MetricDefinition) -> tuple[int, bool]:
        corpus = f"{definition.name} {definition.description} {definition.unit}".lower()
        matches = sum(
            1
            for terms in _METRIC_SYNONYMS.values()
            if any(term in normalized_content for term in terms)
            and any(term in corpus for term in terms)
        )
        return matches, definition.golden_metric

    ranked = sorted(definitions, key=score, reverse=True)
    matching = [definition for definition in ranked if score(definition)[0] > 0]
    return (matching or [definition for definition in ranked if definition.golden_metric])[:limit]


def render_promql(definition: MetricDefinition, entity: dict[str, Any]) -> str:
    fields = entity.get("__fields__", entity.get("fields", {}))
    if not isinstance(fields, dict):
        return definition.promql
    label_values = _resolve_label_values(definition.label_names, fields)
    if not label_values:
        return definition.promql
    return re.sub(
        r"\{([^{}]*)\}", lambda match: _merge_selector(match, label_values), definition.promql
    )


def _resolve_label_values(label_names: Sequence[str], fields: dict[str, Any]) -> dict[str, str]:
    label_values: dict[str, str] = {}
    for label_name in label_names:
        for field_name in _LABEL_FIELD_ALIASES.get(label_name, (label_name,)):
            value = fields.get(field_name)
            if isinstance(value, str | int | float | bool) and str(value):
                label_values[label_name] = str(value)
                break
    return label_values


def _merge_selector(match: re.Match[str], label_values: dict[str, str]) -> str:
    selector = match.group(1)
    existing = [part.strip() for part in selector.split(",") if part.strip()]
    existing_labels = {
        selector_match.group("label")
        for matcher in existing
        if (
            selector_match := re.match(
                r"^(?P<label>[a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|!=|=~|!~)", matcher
            )
        )
    }
    applicable_values = {
        label: value for label, value in label_values.items() if label in existing_labels
    }
    filtered = [
        matcher
        for matcher in existing
        if not any(
            re.match(rf"^{re.escape(label)}\s*(?:=|!=|=~|!~)", matcher)
            for label in applicable_values
        )
    ]
    injected = [f"{label}={json.dumps(value)}" for label, value in applicable_values.items()]
    return "{" + ",".join([*injected, *filtered]) + "}"


def resolve_time_range(
    content: str, default_window_minutes: int, now: datetime | None = None
) -> tuple[str, str]:
    end = now or datetime.now(UTC)
    match = _WINDOW_PATTERN.search(content)
    if match is None:
        duration = timedelta(minutes=default_window_minutes)
    else:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        duration = timedelta(
            minutes=amount if unit in {"m", "min", "分钟"} else 0,
            hours=amount if unit in {"h", "小时"} else 0,
            days=amount if unit in {"d", "天"} else 0,
        )
    start = end - duration
    return start.isoformat(), end.isoformat()


def create_get_metric_node(
    catalog_client: MetricCatalogClient | None,
    gateway_client: MetricGatewayClient | None,
) -> GetMetricNode:
    async def get_metric_node(state: AgentState) -> AgentState:
        default_config = state.default_config
        entity_id = extract_entity_id(state.msg)
        if entity_id is None:
            state.msg = "请先使用 @ 引用目标实体，再执行 /get_metric。"
            return state
        if catalog_client is None or gateway_client is None:
            state.msg = "指标查询依赖未配置，暂时无法获取时序数据。"
            return state
        try:
            entity, dataset_items = await asyncio.gather(
                catalog_client.get_entity(entity_id), catalog_client.get_metric_sets(entity_id)
            )
        except CatalogClientError as exc:
            logger.warning("get_metric_catalog_failed", entity_id=entity_id, error=str(exc))
            state.msg = f"获取 MetricSet 失败：{exc}"
            return state

        definitions = extract_metric_definitions(dataset_items)
        selected = select_metric_definitions(
            definitions,
            state.msg,
            default_config.metric_query_max_definitions,
        )
        if not selected:
            state.msg = "未在该实体关联的 MetricSet 中找到可查询的指标。"
            return state

        start, end = resolve_time_range(
            state.msg,
            default_config.metric_query_default_window_minutes,
        )
        queries = [(definition, render_promql(definition, entity)) for definition in selected]
        results = await asyncio.gather(
            *(
                gateway_client.range_query(
                    query,
                    start=start,
                    end=end,
                    step=default_config.metric_query_step,
                )
                for _, query in queries
            ),
            return_exceptions=True,
        )
        metric_results: list[dict[str, Any]] = []
        for (definition, query), result in zip(queries, results, strict=True):
            if isinstance(result, MCPGatewayClientError):
                metric_results.append(
                    {"metric": definition.name, "promql": query, "error": str(result)}
                )
            elif isinstance(result, Exception):
                metric_results.append(
                    {"metric": definition.name, "promql": query, "error": "指标查询失败"}
                )
            else:
                metric_results.append(
                    {"metric": definition.name, "promql": query, "result": result}
                )
        state.metric_results = metric_results
        state.msg = (
            "指标查询结果：\n```json\n"
            + json.dumps(metric_results, ensure_ascii=False, indent=2)
            + "\n```"
        )
        logger.info("get_metric_completed", entity_id=entity_id, metric_count=len(metric_results))
        return state

    return get_metric_node
