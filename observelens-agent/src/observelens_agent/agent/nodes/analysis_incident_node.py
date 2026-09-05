import asyncio
import json
import re
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

import structlog
from langgraph.config import get_stream_writer

from observelens_agent.agent.nodes.get_info_node import extract_entity_id
from observelens_agent.agent.nodes.get_metric_node import (
    extract_metric_definitions,
    render_promql,
    resolve_time_range,
    select_metric_definitions,
)
from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.catalog import CatalogClientError
from observelens_agent.clients.knowledge import KnowledgeClientError

logger = structlog.get_logger(__name__)

_LOG_ANOMALY_PATTERN = re.compile(
    r"\b(?:error|exception|fatal|panic|timeout|oom|failed?|unavailable)\b|错误|异常|超时|失败|崩溃",
    re.IGNORECASE,
)
_STEPS = (
    ("identify_entity", "识别故障对应实体"),
    ("learn_architecture", "从 RAG 学习系统架构"),
    ("load_semantics", "读取 Catalog 查询语义与拓扑"),
    ("plan_telemetry", "推理待观测遥测数据"),
    ("fetch_telemetry", "获取真实指标与日志数据"),
    ("detect_anomalies", "识别指标和日志异常"),
    ("infer_root_cause", "汇总异常并推理根因"),
    ("build_report", "生成故障报告"),
)


class IncidentCatalogClient(Protocol):
    async def get_entity(self, entity_id: str) -> dict[str, Any]: ...

    async def search_entities(self, keyword: str, limit: int = 5) -> list[dict[str, Any]]: ...

    async def get_datasets(
        self, entity_id: str, dataset_type: str = "all"
    ) -> list[dict[str, Any]]: ...

    async def get_topology(self, entity_id: str, depth: int = 3) -> dict[str, Any]: ...


class IncidentKnowledgeClient(Protocol):
    async def retrieve_architecture(
        self, query: str, entity_type: str | None, entity_name: str | None
    ) -> list[dict[str, Any]]: ...


class IncidentGatewayClient(Protocol):
    async def range_query(self, query: str, start: str, end: str, step: str) -> dict[str, Any]: ...

    async def query_logs(
        self, query: str, start: str, end: str, limit: int = 200
    ) -> dict[str, Any]: ...


IncidentNode = Callable[[AgentState], Awaitable[AgentState]]


class _EventEmitter:
    def __init__(self, conversation_id: str, run_id: str) -> None:
        self._conversation_id = conversation_id
        self._run_id = run_id
        self._sequence = 1
        self._writer: Callable[[dict[str, str]], None] | None
        try:
            self._writer = get_stream_writer()
        except RuntimeError:
            self._writer = None

    def emit(self, event_type: str, data: dict[str, object]) -> None:
        if self._writer is None:
            return
        self._sequence += 1
        payload = {
            "id": f"incident-{self._run_id}-{self._sequence}",
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "conversation_id": self._conversation_id,
            "run_id": self._run_id,
            "sequence": self._sequence,
            "data": data,
        }
        self._writer(
            {
                "sse": (
                    f"event: {event_type}\nid: {payload['id']}\n"
                    f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                )
            }
        )


def _entity_fields(entity: dict[str, Any]) -> dict[str, Any]:
    fields = entity.get("__fields__", entity.get("fields", {}))
    return fields if isinstance(fields, dict) else {}


def _entity_id(entity: dict[str, Any]) -> str | None:
    for key in ("__entity_uuid__", "entity_uuid", "id"):
        value = entity.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _entity_name(entity: dict[str, Any]) -> str | None:
    fields = _entity_fields(entity)
    for key in ("display_name", "name", "id", "service_name", "workload_name"):
        value = fields.get(key)
        if isinstance(value, str) and value:
            return value
    return _entity_id(entity)


def _dataset_document(item: dict[str, Any]) -> dict[str, Any] | None:
    dataset = item.get("dataset")
    if not isinstance(dataset, dict):
        return None
    document = dataset.get("document", dataset)
    return document if isinstance(document, dict) else None


def _extract_log_queries(dataset_items: Sequence[dict[str, Any]]) -> list[str]:
    queries: list[str] = []
    for item in dataset_items:
        document = _dataset_document(item)
        if document is None or document.get("kind") != "LogSet":
            continue
        spec = document.get("spec")
        if not isinstance(spec, dict):
            continue
        for key in ("generator", "query"):
            value = spec.get(key)
            if isinstance(value, str) and value.strip():
                queries.append(value.strip())
        definitions = spec.get("queries")
        if isinstance(definitions, list):
            for definition in definitions:
                if isinstance(definition, dict):
                    value = definition.get("generator", definition.get("query"))
                    if isinstance(value, str) and value.strip():
                        queries.append(value.strip())
    return list(dict.fromkeys(queries))


def _fallback_log_query(entity: dict[str, Any]) -> str | None:
    fields = _entity_fields(entity)
    labels: list[str] = []
    for label, field in (("namespace", "namespace"), ("pod", "pod"), ("pod", "id")):
        value = fields.get(field)
        if (
            isinstance(value, str)
            and value
            and not any(part.startswith(f"{label}=") for part in labels)
        ):
            labels.append(f"{label}={json.dumps(value)}")
    return "{" + ",".join(labels) + "}" if labels else None


def _dataset_summary(dataset_items: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for item in dataset_items:
        document = _dataset_document(item)
        if document is None:
            continue
        metadata = document.get("metadata")
        summary.append(
            {
                "kind": str(document.get("kind", "Dataset")),
                "name": str(metadata.get("name", "unnamed"))
                if isinstance(metadata, dict)
                else "unnamed",
            }
        )
    return summary


def _summarize_architecture(results: Sequence[dict[str, Any]]) -> list[dict[str, object]]:
    return [
        {
            "document": str(item.get("citation", {}).get("document_name", "知识库文档"))
            if isinstance(item.get("citation"), dict)
            else "知识库文档",
            "score": item.get("score", 0),
            "content": str(item.get("content", ""))[:800],
        }
        for item in results
    ]


def _anomalies_from_telemetry(
    metric_results: Sequence[dict[str, Any]], log_results: Sequence[dict[str, Any]]
) -> list[dict[str, str]]:
    anomalies: list[dict[str, str]] = []
    for item in metric_results:
        metric = str(item.get("metric", "指标"))
        if isinstance(item.get("error"), str):
            anomalies.append({"source": metric, "detail": str(item["error"])})
            continue
        result = item.get("result")
        if isinstance(result, dict):
            data = result.get("data")
            if isinstance(data, dict) and data.get("series_count") == 0:
                anomalies.append({"source": metric, "detail": "查询未返回时序数据"})
            for evidence in result.get("evidence", []):
                if isinstance(evidence, dict) and _LOG_ANOMALY_PATTERN.search(
                    str(evidence.get("value", ""))
                ):
                    anomalies.append({"source": metric, "detail": str(evidence.get("value"))})
    for item in log_results:
        if isinstance(item.get("error"), str):
            anomalies.append({"source": "日志", "detail": str(item["error"])})
            continue
        result = item.get("result")
        if not isinstance(result, dict):
            continue
        for evidence in result.get("evidence", []):
            if isinstance(evidence, dict):
                value = str(evidence.get("value", ""))
                if _LOG_ANOMALY_PATTERN.search(value):
                    anomalies.append({"source": "日志", "detail": value[:500]})
    return anomalies[:20]


def _root_cause(anomalies: Sequence[dict[str, str]]) -> tuple[str, str]:
    log_anomalies = [item for item in anomalies if item["source"] == "日志"]
    metric_anomalies = [item for item in anomalies if item["source"] != "日志"]
    if log_anomalies:
        return (
            "高",
            (
                f"日志中检测到 {len(log_anomalies)} 条错误或异常信号，"
                "最可能的根因是应用或依赖调用失败。"
            ),
        )
    if metric_anomalies:
        return (
            "中",
            (
                f"检测到 {len(metric_anomalies)} 项指标异常或数据缺口，"
                "需要结合应用日志进一步确认根因。"
            ),
        )
    return "低", "未发现明确异常证据，当前无法形成可验证的根因结论。"


def _report_markdown(report: dict[str, Any]) -> str:
    anomalies = report["anomalies"]
    anomaly_text = (
        "\n".join(f"- **{item['source']}**：{item['detail']}" for item in anomalies)
        or "- 未检测到明确异常证据。"
    )
    return (
        "# 故障调查报告\n\n"
        f"- **目标实体**：{report['entity_name']} (`{report['entity_id']}`)\n"
        f"- **根因置信度**：{report['confidence']}\n"
        f"- **根因结论**：{report['root_cause']}\n\n"
        "## 异常证据\n"
        f"{anomaly_text}\n\n"
        "## 调查范围\n"
        f"- 架构上下文：{report['architecture_contexts']} 条\n"
        f"- 指标查询：{report['metric_queries']} 条\n"
        f"- 日志查询：{report['log_queries']} 条\n"
        f"- Catalog 数据集：{report['datasets']} 个\n"
        f"- 拓扑节点：{report['topology_nodes']} 个\n"
    )


def create_analysis_incident_node(
    catalog_client: IncidentCatalogClient | None,
    knowledge_client: IncidentKnowledgeClient | None,
    gateway_client: IncidentGatewayClient | None,
) -> IncidentNode:
    async def analysis_incident_node(state: AgentState) -> AgentState:
        default_config = state.default_config
        emitter = _EventEmitter(state.conversation_id or "conversation", state.run_id or "run")
        emitter.emit(
            "analysis.generated",
            {"content": "已启动故障调查，将依次识别实体、学习架构、查询遥测并生成根因报告。"},
        )
        emitter.emit(
            "plan.generated",
            {
                "title": "Incident Investigation",
                "steps": [{"id": key, "title": title} for key, title in _STEPS],
            },
        )
        if catalog_client is None:
            state.msg = "故障调查依赖 Observability Data Catalog，当前未配置。"
            state.run_failure_message = state.msg
            emitter.emit("step.failed", {"step_id": "identify_entity", "title": _STEPS[0][1]})
            return state

        emitter.emit("step.started", {"step_id": "identify_entity", "title": _STEPS[0][1]})
        entity_id = extract_entity_id(state.msg)
        try:
            if entity_id:
                entity = await catalog_client.get_entity(entity_id)
            else:
                candidates = await catalog_client.search_entities(state.msg)
                if not candidates or (entity_id := _entity_id(candidates[0])) is None:
                    raise CatalogClientError("未能从请求中识别到故障实体")
                entity = await catalog_client.get_entity(entity_id)
        except CatalogClientError as exc:
            state.msg = f"故障实体识别失败：{exc}"
            state.run_failure_message = state.msg
            emitter.emit("step.failed", {"step_id": "identify_entity", "title": _STEPS[0][1]})
            return state
        entity_id = _entity_id(entity) or entity_id
        if entity_id is None:
            state.msg = "故障实体识别失败：Catalog 返回的数据不含实体 ID。"
            state.run_failure_message = state.msg
            emitter.emit("step.failed", {"step_id": "identify_entity", "title": _STEPS[0][1]})
            return state
        entity_name = _entity_name(entity) or entity_id
        entity_type = entity.get("__entity_type__")
        state.entity_details = entity
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-entity",
                "observation_type": "json",
                "title": "故障实体",
                "summary": f"已识别目标实体 {entity_name}",
                "content": {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "fields": _entity_fields(entity),
                },
            },
        )
        emitter.emit(
            "step.completed", {"step_id": "identify_entity", "summary": f"已识别 {entity_name}"}
        )

        emitter.emit("step.started", {"step_id": "learn_architecture", "title": _STEPS[1][1]})
        architecture_contexts: list[dict[str, Any]] = []
        if knowledge_client is None:
            architecture_summary = "知识库未配置，跳过架构上下文检索。"
        else:
            try:
                architecture_contexts = await knowledge_client.retrieve_architecture(
                    f"{entity_name} 系统架构、上下游依赖与故障排查手册：{state.msg}",
                    entity_type if isinstance(entity_type, str) else None,
                    entity_name,
                )
                architecture_summary = f"检索到 {len(architecture_contexts)} 条架构上下文。"
            except KnowledgeClientError as exc:
                architecture_summary = f"知识库检索不可用：{exc}"
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-architecture",
                "observation_type": "table",
                "title": "系统架构上下文",
                "summary": architecture_summary,
                "content": {"contexts": _summarize_architecture(architecture_contexts)},
            },
        )
        emitter.emit(
            "step.completed", {"step_id": "learn_architecture", "summary": architecture_summary}
        )

        emitter.emit("step.started", {"step_id": "load_semantics", "title": _STEPS[2][1]})
        datasets: list[dict[str, Any]] = []
        topology: dict[str, Any] = {}
        try:
            datasets, topology = await asyncio.gather(
                catalog_client.get_datasets(entity_id), catalog_client.get_topology(entity_id)
            )
            semantic_summary = (
                f"读取到 {len(datasets)} 个 Dataset 和 "
                f"{len(topology.get('nodes', []))} 个拓扑节点。"
            )
        except CatalogClientError as exc:
            semantic_summary = f"Catalog 查询语义或拓扑读取失败：{exc}"
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-catalog-semantics",
                "observation_type": "json",
                "title": "Catalog 查询语义与拓扑",
                "summary": semantic_summary,
                "content": {"datasets": _dataset_summary(datasets), "topology": topology},
            },
        )
        emitter.emit("step.completed", {"step_id": "load_semantics", "summary": semantic_summary})

        emitter.emit("step.started", {"step_id": "plan_telemetry", "title": _STEPS[3][1]})
        definitions = extract_metric_definitions(datasets)
        selected_metrics = select_metric_definitions(
            definitions,
            state.msg,
            default_config.metric_query_max_definitions,
        )
        metric_queries = [(item, render_promql(item, entity)) for item in selected_metrics]
        log_queries = _extract_log_queries(datasets)
        if not log_queries:
            fallback_log_query = _fallback_log_query(entity)
            if fallback_log_query:
                log_queries = [fallback_log_query]
        start, end = resolve_time_range(
            state.msg,
            default_config.metric_query_default_window_minutes,
        )
        telemetry_summary = (
            f"计划查询 {len(metric_queries)} 个指标和 {len(log_queries)} 条日志语义。"
        )
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-telemetry-plan",
                "observation_type": "json",
                "title": "遥测调查计划",
                "summary": telemetry_summary,
                "content": {
                    "time_range": {"start": start, "end": end},
                    "metrics": [
                        {"name": item.name, "promql": query} for item, query in metric_queries
                    ],
                    "logs": log_queries,
                },
            },
        )
        emitter.emit("step.completed", {"step_id": "plan_telemetry", "summary": telemetry_summary})

        emitter.emit("step.started", {"step_id": "fetch_telemetry", "title": _STEPS[4][1]})
        metric_results: list[dict[str, Any]] = []
        log_results: list[dict[str, Any]] = []
        if gateway_client is None:
            fetch_summary = "MCP Gateway 未配置，未执行真实遥测查询。"
        else:
            emitter.emit("toolcall.started", {"tool": "prom_range_query"})
            metric_values = await asyncio.gather(
                *(
                    gateway_client.range_query(
                        query,
                        start,
                        end,
                        default_config.metric_query_step,
                    )
                    for _, query in metric_queries
                ),
                return_exceptions=True,
            )
            for (definition, query), value in zip(metric_queries, metric_values, strict=True):
                metric_results.append(
                    {"metric": definition.name, "promql": query, "error": str(value)}
                    if isinstance(value, Exception)
                    else {"metric": definition.name, "promql": query, "result": value}
                )
            emitter.emit("toolcall.completed", {"tool": "prom_range_query"})
            if log_queries:
                emitter.emit("toolcall.started", {"tool": "loki_query_logs"})
                log_values = await asyncio.gather(
                    *(
                        gateway_client.query_logs(
                            query,
                            start,
                            end,
                            default_config.incident_log_query_limit,
                        )
                        for query in log_queries
                    ),
                    return_exceptions=True,
                )
                for query, value in zip(log_queries, log_values, strict=True):
                    log_results.append(
                        {"query": query, "error": str(value)}
                        if isinstance(value, Exception)
                        else {"query": query, "result": value}
                    )
                emitter.emit("toolcall.completed", {"tool": "loki_query_logs"})
            fetch_summary = f"已完成 {len(metric_results)} 个指标和 {len(log_results)} 条日志查询。"
        state.metric_results = metric_results
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-telemetry-results",
                "observation_type": "json",
                "title": "真实遥测数据",
                "summary": fetch_summary,
                "content": {"metrics": metric_results, "logs": log_results},
            },
        )
        emitter.emit("step.completed", {"step_id": "fetch_telemetry", "summary": fetch_summary})

        emitter.emit("step.started", {"step_id": "detect_anomalies", "title": _STEPS[5][1]})
        anomalies = _anomalies_from_telemetry(metric_results, log_results)
        anomaly_summary = f"识别到 {len(anomalies)} 条异常证据。"
        emitter.emit(
            "observation.generated",
            {
                "id": "incident-anomalies",
                "observation_type": "table",
                "title": "异常证据",
                "summary": anomaly_summary,
                "content": {"anomalies": anomalies},
            },
        )
        emitter.emit("step.completed", {"step_id": "detect_anomalies", "summary": anomaly_summary})

        emitter.emit("step.started", {"step_id": "infer_root_cause", "title": _STEPS[6][1]})
        confidence, root_cause = _root_cause(anomalies)
        emitter.emit(
            "finding.generated",
            {
                "id": "incident-root-cause",
                "category": "issue" if anomalies else "risk",
                "title": "根因推理",
                "analysis": root_cause,
            },
        )
        emitter.emit("step.completed", {"step_id": "infer_root_cause", "summary": root_cause})

        emitter.emit("step.started", {"step_id": "build_report", "title": _STEPS[7][1]})
        report = {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "architecture_contexts": len(architecture_contexts),
            "datasets": len(datasets),
            "topology_nodes": len(topology.get("nodes", [])),
            "metric_queries": len(metric_results),
            "log_queries": len(log_results),
            "anomalies": anomalies,
            "confidence": confidence,
            "root_cause": root_cause,
        }
        state.incident_report = report
        state.msg = _report_markdown(report)
        emitter.emit("output.started", {"format": "markdown"})
        emitter.emit("output.progress", {"format": "markdown", "content": state.msg})
        emitter.emit("output.completed", {"format": "markdown", "content": state.msg})
        emitter.emit("step.completed", {"step_id": "build_report", "summary": "故障报告已生成。"})
        logger.info(
            "analysis_incident_completed", entity_id=entity_id, anomaly_count=len(anomalies)
        )
        return state

    return analysis_incident_node
