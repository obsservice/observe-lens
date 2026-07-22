from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.common.context import RequestContext
from observelens_service.common.exceptions import ResourceNotFoundError
from observelens_service.modules.conversations.service import new_id
from observelens_service.modules.inspections.models import (
    InspectionModel,
    InspectionRunModel,
    InspectionScheduleModel,
)
from observelens_service.modules.inspections.repository import InspectionRepository
from observelens_service.modules.inspections.schemas import (
    InspectionCreateRequest,
    InspectionExecutionResponse,
    InspectionPage,
    InspectionResponse,
    InspectionUpdateRequest,
)


class InspectionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = InspectionRepository(session)

    async def list(self, context: RequestContext, page: int, page_size: int) -> InspectionPage:
        tasks, total = await self._repository.list(context.tenant_id, page, page_size)
        items = [await self._response(context.tenant_id, task) for task in tasks]
        return InspectionPage(items=items, total=total, page=page, page_size=page_size)

    async def create(
        self, context: RequestContext, request: InspectionCreateRequest
    ) -> InspectionResponse:
        task = InspectionModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            name=request.name,
            description=request.description,
            scope=request.scope,
            input_template=request.input_template,
            enabled=request.enabled,
            create_by=context.user_id,
        )
        schedule = self._new_schedule(context.tenant_id, task.id, request.schedule, request.enabled)
        self._repository.add(task)
        self._repository.add(schedule)
        await self._session.flush()
        return await self._response(context.tenant_id, task)

    async def get(self, context: RequestContext, inspection_id: int) -> InspectionResponse:
        return await self._response(context.tenant_id, await self._require(context, inspection_id))

    async def update(
        self, context: RequestContext, inspection_id: int, request: InspectionUpdateRequest
    ) -> InspectionResponse:
        task = await self._require(context, inspection_id)
        for field in ("name", "description", "scope", "input_template"):
            value = getattr(request, field)
            if value is not None:
                setattr(task, field, value)
        if request.schedule is not None:
            schedule = await self._repository.schedule(context.tenant_id, task.id)
            if schedule is not None:
                self._set_schedule(schedule, request.schedule)
        task.update_by = context.user_id
        await self._session.flush()
        return await self._response(context.tenant_id, task)

    async def delete(self, context: RequestContext, inspection_id: int) -> None:
        task = await self._require(context, inspection_id)
        task.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def set_enabled(
        self, context: RequestContext, inspection_id: int, enabled: bool
    ) -> InspectionResponse:
        task = await self._require(context, inspection_id)
        task.enabled = enabled
        schedule = await self._repository.schedule(context.tenant_id, task.id)
        if schedule is not None:
            schedule.enabled = enabled
        await self._session.flush()
        return await self._response(context.tenant_id, task)

    async def execute(
        self, context: RequestContext, inspection_id: int
    ) -> InspectionExecutionResponse:
        await self._require(context, inspection_id)
        run = InspectionRunModel(
            id=new_id(),
            tenant_id=context.tenant_id,
            task_id=inspection_id,
            trigger_type="MANUAL",
            status="PENDING",
        )
        self._repository.add(run)
        await self._session.flush()
        return InspectionExecutionResponse(run_id=run.id, status="PENDING")

    async def _require(self, context: RequestContext, inspection_id: int) -> InspectionModel:
        task = await self._repository.get(context.tenant_id, inspection_id)
        if task is None:
            raise ResourceNotFoundError("Inspection")
        return task

    async def _response(self, tenant_id: int, task: InspectionModel) -> InspectionResponse:
        schedule = await self._repository.schedule(tenant_id, task.id)
        last_run = await self._repository.last_run(tenant_id, task.id)
        return InspectionResponse.model_validate(
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "scope": task.scope,
                "schedule": self._schedule_text(schedule),
                "status": "ENABLED" if task.enabled else "DISABLED",
                "last_run_at": last_run.create_time if last_run else None,
                "create_time": task.create_time,
                "update_time": task.update_time,
            }
        )

    @staticmethod
    def _new_schedule(
        tenant_id: int, task_id: int, value: str, enabled: bool
    ) -> InspectionScheduleModel:
        schedule = InspectionScheduleModel(
            id=new_id(),
            tenant_id=tenant_id,
            task_id=task_id,
            schedule_type="INTERVAL",
            enabled=enabled,
        )
        InspectionService._set_schedule(schedule, value)
        return schedule

    @staticmethod
    def _set_schedule(schedule: InspectionScheduleModel, value: str) -> None:
        if value.upper().startswith("CRON:"):
            schedule.schedule_type, schedule.cron_expression, schedule.interval_seconds = (
                "CRON",
                value[5:].strip(),
                None,
            )
        else:
            intervals = {"EVERY HOUR": 3600, "EVERY DAY": 86400}
            schedule.schedule_type, schedule.interval_seconds, schedule.cron_expression = (
                "INTERVAL",
                intervals.get(value.upper(), 3600),
                None,
            )

    @staticmethod
    def _schedule_text(schedule: InspectionScheduleModel | None) -> str:
        if schedule is None:
            return "Every Hour"
        return (
            f"CRON: {schedule.cron_expression}"
            if schedule.schedule_type == "CRON"
            else "Every Day"
            if schedule.interval_seconds == 86400
            else "Every Hour"
        )
