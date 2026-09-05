import asyncio
from typing import Any

import structlog

from observelens_agent.agent.nodes.get_info_node import extract_entity_id
from observelens_agent.agent.nodes.get_metric_node import (
    extract_metric_definitions,
    render_promql,
    select_metric_definitions,
)
from observelens_agent.agent.nodes.rca_node_common import (
    RCA_PIPELINE_STEPS,
    IncidentCatalogClient,
    IncidentKnowledgeClient,
    RCAStageNode,
    emit_rca_event,
    entity_id,
    entity_name,
    extract_log_queries,
    fallback_log_query,
)
from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.catalog import CatalogClientError
from observelens_agent.clients.knowledge import KnowledgeClientError

logger = structlog.get_logger(__name__)


def create_planner_node(
    catalog_client: IncidentCatalogClient | None, knowledge_client: IncidentKnowledgeClient | None
) -> RCAStageNode:
    """Create an RCA planner that resolves the target and builds collection queries."""

    async def planner_node(state: AgentState) -> AgentState:
        emit_rca_event(state, "analysis.generated", {"content": "已启动根因分析流水线。"})
        emit_rca_event(
            state,
            "plan.generated",
            {
                "title": "Root Cause Analysis",
                "steps": [{"id": key, "title": title} for key, title in RCA_PIPELINE_STEPS],
            },
        )
        emit_rca_event(
            state, "step.started", {"step_id": "planner", "title": RCA_PIPELINE_STEPS[0][1]}
        )
        if catalog_client is None:
            state.msg = "根因分析依赖 Observability Data Catalog，当前未配置。"
            state.run_failure_message = state.msg
            emit_rca_event(
                state, "step.failed", {"step_id": "planner", "title": RCA_PIPELINE_STEPS[0][1]}
            )
            return state
        try:
            target_id = extract_entity_id(state.msg)
            if target_id is None:
                candidates = await catalog_client.search_entities(
                    state.entity or state.msg, limit=1
                )
                target_id = entity_id(candidates[0]) if candidates else None
            if target_id is None:
                raise CatalogClientError("未找到可分析的目标实体")
            entity, datasets, topology = await asyncio.gather(
                catalog_client.get_entity(target_id),
                catalog_client.get_datasets(target_id),
                catalog_client.get_topology(target_id),
            )
        except CatalogClientError as exc:
            state.msg = f"根因分析无法解析目标实体：{exc}"
            state.run_failure_message = state.msg
            emit_rca_event(
                state, "step.failed", {"step_id": "planner", "title": RCA_PIPELINE_STEPS[0][1]}
            )
            return state
        target_name = entity_name(entity) or target_id
        architecture_contexts: list[dict[str, Any]] = []
        if knowledge_client is not None:
            try:
                architecture_contexts = await knowledge_client.retrieve_architecture(
                    state.msg,
                    str(entity.get("__entity_type__")) if entity.get("__entity_type__") else None,
                    target_name,
                )
            except KnowledgeClientError as exc:
                logger.warning("rca_planner_rag_failed", error=str(exc))
        selected = select_metric_definitions(
            extract_metric_definitions(datasets),
            state.msg,
            state.default_config.metric_query_max_definitions,
        )
        metric_queries = [
            {"metric": definition.name, "query": render_promql(definition, entity)}
            for definition in selected
        ]
        log_queries = extract_log_queries(datasets)
        if not log_queries and (fallback := fallback_log_query(entity)):
            log_queries.append(fallback)
        state.rca_context.update(
            {
                "entity_id": target_id,
                "entity_name": target_name,
                "architecture_contexts": architecture_contexts,
                "datasets": datasets,
                "topology": topology,
                "metric_queries": metric_queries,
                "log_queries": log_queries,
            }
        )
        emit_rca_event(
            state,
            "observation.generated",
            {
                "id": "rca-plan",
                "observation_type": "json",
                "title": "执行计划",
                "content": {"metrics": metric_queries, "logs": log_queries},
            },
        )
        emit_rca_event(
            state, "step.completed", {"step_id": "planner", "summary": "根因分析执行计划已生成。"}
        )
        return state

    return planner_node
