import json
import re
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

from langgraph.config import get_stream_writer

from observelens_agent.agent.state.state import AgentState

RCA_PIPELINE_STEPS = (
    ("planner", "分析根因分析执行计划"),
    ("evidence", "收集可观测推理证据"),
    ("hypothesis", "生成根因假设"),
    ("judge", "校验根因假设"),
    ("report", "生成根因分析报告"),
)
_LOG_ANOMALY_PATTERN = re.compile(
    r"\b(?:error|exception|fatal|panic|timeout|oom|failed?|unavailable)\b|错误|异常|超时|失败|崩溃",
    re.IGNORECASE,
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


RCAStageNode = Callable[[AgentState], Awaitable[AgentState]]


def emit_rca_event(state: AgentState, event_type: str, data: dict[str, object]) -> None:
    try:
        writer: Callable[[dict[str, str]], None] | None = get_stream_writer()
    except RuntimeError:
        writer = None
    if writer is None:
        return
    sequence = int(state.rca_context.get("event_sequence", 0)) + 1
    state.rca_context["event_sequence"] = sequence
    run_id = state.run_id or "run"
    payload = {
        "id": f"rca-{run_id}-{sequence}",
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "conversation_id": state.conversation_id or "conversation",
        "run_id": run_id,
        "sequence": sequence,
        "data": data,
    }
    sse = (
        f"event: {event_type}\nid: {payload['id']}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    )
    writer({"sse": sse})


def entity_id(entity: dict[str, Any]) -> str | None:
    for key in ("__entity_uuid__", "entity_uuid", "id"):
        if isinstance(value := entity.get(key), str) and value:
            return value
    return None


def entity_name(entity: dict[str, Any]) -> str | None:
    fields = entity.get("__fields__", entity.get("fields", {}))
    if isinstance(fields, dict):
        for key in ("display_name", "name", "id", "service_name", "workload_name"):
            if isinstance(value := fields.get(key), str) and value:
                return value
    return entity_id(entity)


def extract_log_queries(dataset_items: Sequence[dict[str, Any]]) -> list[str]:
    queries: list[str] = []
    for item in dataset_items:
        dataset = item.get("dataset")
        document = dataset.get("document", dataset) if isinstance(dataset, dict) else None
        if not isinstance(document, dict) or document.get("kind") != "LogSet":
            continue
        spec = document.get("spec")
        if isinstance(spec, dict):
            for key in ("generator", "query"):
                if isinstance(value := spec.get(key), str) and value.strip():
                    queries.append(value.strip())
    return list(dict.fromkeys(queries))


def fallback_log_query(entity: dict[str, Any]) -> str | None:
    fields = entity.get("__fields__", entity.get("fields", {}))
    if not isinstance(fields, dict):
        return None
    labels = [
        f"{key}={json.dumps(value)}"
        for key in ("namespace", "pod", "id")
        if isinstance(value := fields.get(key), str) and value
    ]
    return "{" + ",".join(dict.fromkeys(labels)) + "}" if labels else None


def anomalies_from_evidence(
    metric_results: Sequence[dict[str, Any]], log_results: Sequence[dict[str, Any]]
) -> list[dict[str, str]]:
    anomalies: list[dict[str, str]] = []
    for item in metric_results:
        metric = str(item.get("metric", "指标"))
        if isinstance(item.get("error"), str):
            anomalies.append({"source": metric, "detail": str(item["error"])})
        elif (
            isinstance(result := item.get("result"), dict)
            and isinstance(data := result.get("data"), dict)
            and data.get("series_count") == 0
        ):
            anomalies.append({"source": metric, "detail": "查询未返回时序数据"})
    for item in log_results:
        if isinstance(result := item.get("result"), dict):
            for evidence in result.get("evidence", []):
                if isinstance(evidence, dict) and _LOG_ANOMALY_PATTERN.search(
                    value := str(evidence.get("value", ""))
                ):
                    anomalies.append({"source": "日志", "detail": value[:500]})
    return anomalies[:20]


def build_hypothesis(anomalies: Sequence[dict[str, str]]) -> tuple[str, str]:
    if any(item["source"] == "日志" for item in anomalies):
        return "高", "日志错误信号表明应用或依赖调用失败是最可能根因。"
    if anomalies:
        return "中", "指标异常表明服务运行存在风险，需要补充日志或 Trace 证据确认根因。"
    return "低", "未发现明确异常证据，当前无法形成可验证的根因结论。"
