import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.clients.agent import AgentClient
from observelens_service.database.session import session_scope
from observelens_service.modules.inspections.repository import InspectionRepository

logger = structlog.get_logger(__name__)


async def execute_inspection_agent(
    agent_client: AgentClient,
    factory: async_sessionmaker[AsyncSession],
    tenant_id: int,
    task_id: int,
    run_id: int,
    content: str,
) -> None:
    status = "SUCCESS"
    try:
        async for _ in agent_client.stream_run(task_id, run_id, content):
            pass
    except Exception:
        status = "FAILED"
        logger.exception("inspection_agent_execution_failed", run_id=run_id, task_id=task_id)

    async with session_scope(factory) as session:
        run = await InspectionRepository(session).get_run(tenant_id, run_id)
        if run is not None:
            run.status = status
            await session.flush()
