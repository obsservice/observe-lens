"""Mock data node — generates AESP demo events for frontend integration."""

import asyncio
import json
from typing import Any

import structlog
from langgraph.config import get_stream_writer

from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)

_BASE_TS = "2026-07-30T10:00:00.000+08:00"


def _envelope(
    seq: int,
    event_type: str,
    run_id: str,
    conversation_id: str,
    data: dict[str, object],
) -> str:
    payload = {
        "id": f"evt_{seq:03d}",
        "type": event_type,
        "timestamp": _BASE_TS,
        "conversation_id": conversation_id,
        "run_id": run_id,
        "sequence": seq,
        "data": data,
    }
    return json.dumps(payload, ensure_ascii=False)


def _sse(
    event_type: str, data: dict[str, object], seq: int, run_id: str, conversation_id: str
) -> str:
    body = _envelope(seq, event_type, run_id, conversation_id, data)
    return f"event: {event_type}\nid: evt_{seq:03d}\ndata: {body}\n\n"


async def mock_node(state: AgentState) -> AgentState:
    """Generate AESP demo events and stream them in real-time via StreamWriter."""
    logger.info("mock_node_executed", msg=state.msg)

    conversation_id = state.conversation_id or "conv_mock"
    run_id = state.run_id or "run_mock"
    writer = get_stream_writer()

    seq = 0

    def emit(event_type: str, data: dict[str, object]) -> None:
        nonlocal seq
        seq += 1
        sse = _sse(event_type, data, seq, run_id, conversation_id)
        writer({"sse": sse})

    # 1. Run started
    emit("run.started", {"agent": "k8s-inspection"})
    await asyncio.sleep(0.1)

    # 2. Analysis
    emit(
        "analysis.generated",
        {
            "content": "识别到当前任务为 Kubernetes 集群巡检，"
            "将检查节点状态、资源水位和异常事件。",
        },
    )
    await asyncio.sleep(0.35)

    # 3. Plan
    emit(
        "plan.generated",
        {
            "title": "Kubernetes Cluster Inspection",
            "steps": [
                {"id": "step_nodes", "title": "检查节点状态"},
                {"id": "step_resources", "title": "检查资源水位"},
                {"id": "step_events", "title": "检查异常事件"},
            ],
        },
    )
    await asyncio.sleep(0.15)

    # --- Step 1: 节点状态 ---
    emit("step.started", {"step_id": "step_nodes", "title": "检查节点状态"})
    await asyncio.sleep(0.1)

    emit("toolcall.started", {"tool": "list_nodes"})
    await asyncio.sleep(0.2)
    emit("toolcall.completed", {"tool": "list_nodes", "duration_ms": 182})
    await asyncio.sleep(0.5)

    emit(
        "observation.generated",
        {
            "id": "obs_nodes",
            "observation_type": "table",
            "title": "Node Status",
            "summary": "集群节点状态一览",
            "content": {
                "columns": ["Node", "Status", "Roles"],
                "rows": [
                    ["node-prod-01", "Ready", "master"],
                    ["node-prod-02", "Ready", "worker"],
                    ["node-prod-03", "SchedulingDisabled", "worker"],
                ],
            },
        },
    )
    await asyncio.sleep(0.45)

    emit(
        "finding.generated",
        {
            "id": "finding_nodes",
            "category": "issue",
            "title": "发现不可调度节点",
            "analysis": "发现 1 个节点处于 SchedulingDisabled，"
            "建议检查节点维护状态或资源压力。",
            "source_observation_ids": ["obs_nodes"],
        },
    )
    await asyncio.sleep(0.6)

    emit("step.completed", {"step_id": "step_nodes", "summary": "节点检查完成。"})
    await asyncio.sleep(0.15)

    # --- Step 2: 资源水位 ---
    emit("step.started", {"step_id": "step_resources", "title": "检查资源水位"})
    await asyncio.sleep(0.1)

    emit("toolcall.started", {"tool": "query_metrics"})
    await asyncio.sleep(0.2)
    emit("toolcall.completed", {"tool": "query_metrics", "duration_ms": 305})
    await asyncio.sleep(0.7)

    emit(
        "observation.generated",
        {
            "id": "obs_cpu",
            "observation_type": "chart",
            "title": "CPU Usage",
            "summary": "最近 30 分钟 CPU 使用率变化",
            "content": {
                "chart_type": "line",
                "x_axis": ["10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30"],
                "series": [
                    {"name": "node-prod-01", "values": [72, 75, 78, 82, 85, 88, 90]},
                    {"name": "node-prod-02", "values": [45, 48, 50, 52, 55, 58, 60]},
                ],
            },
        },
    )
    await asyncio.sleep(0.15)

    emit(
        "finding.generated",
        {
            "id": "finding_cpu",
            "category": "risk",
            "title": "CPU Usage High",
            "analysis": "node-prod-01 CPU 使用率持续超过 85%，存在调度失败风险。",
            "source_observation_ids": ["obs_cpu"],
        },
    )
    await asyncio.sleep(0.8)

    emit("step.completed", {"step_id": "step_resources", "summary": "资源水位检查完成。"})
    await asyncio.sleep(0.15)

    # --- Step 3: 异常事件 ---
    emit("step.started", {"step_id": "step_events", "title": "检查异常事件"})
    await asyncio.sleep(0.1)

    emit("toolcall.started", {"tool": "list_events"})
    await asyncio.sleep(0.4)
    emit("toolcall.completed", {"tool": "list_events", "duration_ms": 143})
    await asyncio.sleep(0.1)

    emit(
        "observation.generated",
        {
            "id": "obs_events",
            "observation_type": "log",
            "title": "Warning Events",
            "summary": "最近 30 分钟 Warning 级别事件",
            "content": {
                "lines": [
                    "10:02:15  Warning  node-prod-03  NodeNotSchedulable",
                    "10:18:42  Warning  node-prod-01  EvictionThresholdMet",
                ],
            },
        },
    )
    await asyncio.sleep(0.35)

    emit(
        "finding.generated",
        {
            "id": "finding_events",
            "category": "anomaly",
            "title": "异常事件检测",
            "analysis": "node-prod-01 在 10:18 触发 EvictionThresholdMet，"
            "与 CPU 持续高水位高度一致。",
            "source_observation_ids": ["obs_events"],
        },
    )
    await asyncio.sleep(0.4)

    emit("step.completed", {"step_id": "step_events", "summary": "异常事件检查完成。"})
    await asyncio.sleep(0.15)

    # --- Output ---
    emit("output.started", {"format": "markdown"})
    await asyncio.sleep(0.5)

    for delta in [
        "## 巡检结果\n\n本次巡检共发现 ",
        "**2 个风险项**，其中 **1 个高风险**。\n\n",
        "### 高风险\n- node-prod-01 CPU 持续超过 85%，已触发驱逐阈值\n\n",
        "### 中风险\n- node-prod-03 处于 SchedulingDisabled\n\n",
        "建议优先处理 node-prod-01 的资源压力问题。",
    ]:
        emit("output.progress", {"format": "markdown", "content": delta})
        await asyncio.sleep(0.08)

    emit(
        "output.completed",
        {
            "format": "markdown",
            "content": (
                "## 巡检结果\n\n"
                "本次巡检共发现 **2 个风险项**，其中 **1 个高风险**。\n\n"
                "### 高风险\n- node-prod-01 CPU 持续超过 85%，已触发驱逐阈值\n\n"
                "### 中风险\n- node-prod-03 处于 SchedulingDisabled\n\n"
                "建议优先处理 node-prod-01 的资源压力问题。"
            ),
            "source_finding_ids": ["finding_nodes", "finding_cpu", "finding_events"],
        },
    )
    await asyncio.sleep(0.1)

    # Run completed
    emit("run.completed", {"duration_ms": 4287})

    state.msg = "[mock] AESP demo stream"
    return state


def extract_sse(chunk: dict[str, Any]) -> str | None:
    """Extract SSE string from a custom stream chunk."""
    if isinstance(chunk, dict) and "sse" in chunk:
        return str(chunk["sse"])

    return None
