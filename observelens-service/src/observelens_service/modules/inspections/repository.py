from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.modules.inspections.models import (
    InspectionModel,
    InspectionRunModel,
    InspectionScheduleModel,
)


class InspectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, tenant_id: int, page: int, page_size: int
    ) -> tuple[list[InspectionModel], int]:
        filters = (InspectionModel.tenant_id == tenant_id, InspectionModel.delete_time.is_(None))
        query: Select[tuple[InspectionModel]] = (
            select(InspectionModel).where(*filters).order_by(InspectionModel.update_time.desc())
        )
        items = (
            await self._session.scalars(query.offset((page - 1) * page_size).limit(page_size))
        ).all()
        total = await self._session.scalar(
            select(func.count()).select_from(InspectionModel).where(*filters)
        )
        return [*items], total or 0

    async def get(self, tenant_id: int, inspection_id: int) -> InspectionModel | None:
        result = await self._session.scalar(
            select(InspectionModel).where(
                InspectionModel.tenant_id == tenant_id,
                InspectionModel.id == inspection_id,
                InspectionModel.delete_time.is_(None),
            )
        )
        return result

    async def schedule(self, tenant_id: int, task_id: int) -> InspectionScheduleModel | None:
        result = await self._session.scalar(
            select(InspectionScheduleModel).where(
                InspectionScheduleModel.tenant_id == tenant_id,
                InspectionScheduleModel.task_id == task_id,
            )
        )
        return result

    async def last_run(self, tenant_id: int, task_id: int) -> InspectionRunModel | None:
        result = await self._session.scalar(
            select(InspectionRunModel)
            .where(InspectionRunModel.tenant_id == tenant_id, InspectionRunModel.task_id == task_id)
            .order_by(InspectionRunModel.create_time.desc())
        )
        return result

    def add(self, model: InspectionModel | InspectionScheduleModel | InspectionRunModel) -> None:
        self._session.add(model)
