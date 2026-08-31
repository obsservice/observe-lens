import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import structlog

from observelens_agent.agent.state.state import AgentState
from observelens_agent.clients.catalog import CatalogClientError

logger = structlog.get_logger(__name__)

_ENTITY_ID_PATTERN = re.compile(r"\bentity_id\s*[=:]\s*([A-Za-z0-9_.:-]+)", re.IGNORECASE)


class CatalogEntityClient(Protocol):
    async def get_entity(self, entity_id: str) -> dict[str, Any]: ...


GetInfoNode = Callable[[AgentState], Awaitable[AgentState]]


def extract_entity_id(content: str) -> str | None:
    match = _ENTITY_ID_PATTERN.search(content)
    return match.group(1) if match else None


def _format_entity_details(entity: dict[str, Any]) -> str:
    return "资源详情：\n```json\n" + json.dumps(entity, ensure_ascii=False, indent=2) + "\n```"


def create_get_info_node(catalog_client: CatalogEntityClient | None) -> GetInfoNode:
    async def get_info_node(state: AgentState) -> AgentState:
        entity_id = extract_entity_id(state.msg)
        if entity_id is None:
            state.msg = "请先使用 @ 引用目标实体，再执行 /get_info。"
            return state
        if catalog_client is None:
            state.msg = "Observability Data Catalog 未配置，暂时无法获取资源详情。"
            return state

        try:
            entity = await catalog_client.get_entity(entity_id)
        except CatalogClientError as exc:
            logger.warning("get_info_catalog_failed", entity_id=entity_id, error=str(exc))
            state.msg = f"获取资源详情失败：{exc}"
            return state

        state.entity_details = entity
        state.msg = _format_entity_details(entity)
        logger.info("get_info_catalog_completed", entity_id=entity_id)
        return state

    return get_info_node
