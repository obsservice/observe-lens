from uuid import UUID

from observelens_knowledge_base.common.context import RequestContext
from observelens_knowledge_base.common.enums import IndexTaskStatus
from observelens_knowledge_base.common.exceptions import ResourceNotFoundError
from observelens_knowledge_base.documents.schemas import IndexTaskResponse
from observelens_knowledge_base.index_tasks.repository import IndexTaskRepository


class IndexTaskService:
    def __init__(self, repository: IndexTaskRepository) -> None:
        self.repository = repository

    async def get(self, ctx: RequestContext, task_id: UUID) -> IndexTaskResponse:
        task = await self.repository.get(ctx.tenant_id, task_id)
        if task is None:
            raise ResourceNotFoundError("DOCUMENT_INDEX_FAILED", "Index task")
        return IndexTaskResponse.model_validate(task)

    async def retry(self, ctx: RequestContext, task_id: UUID) -> IndexTaskResponse:
        task = await self.repository.get(ctx.tenant_id, task_id)
        if task is None:
            raise ResourceNotFoundError("DOCUMENT_INDEX_FAILED", "Index task")
        task.status = IndexTaskStatus.PENDING
        task.retry_count += 1
        task.error_message = None
        task.started_at = None
        task.finished_at = None
        await self.repository.session.flush()
        return IndexTaskResponse.model_validate(task)
