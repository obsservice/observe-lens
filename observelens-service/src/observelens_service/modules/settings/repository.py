from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.modules.settings.models import ModelConfigModel, NotificationModel


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def model(self, tenant_id: int, item_id: int) -> ModelConfigModel | None:
        return await self._session.scalar(
            select(ModelConfigModel).where(
                ModelConfigModel.tenant_id == tenant_id,
                ModelConfigModel.id == item_id,
                ModelConfigModel.delete_time.is_(None),
            )
        )

    async def models(
        self, tenant_id: int, page: int, size: int
    ) -> tuple[list[ModelConfigModel], int]:
        where = (ModelConfigModel.tenant_id == tenant_id, ModelConfigModel.delete_time.is_(None))
        items = (
            await self._session.scalars(
                select(ModelConfigModel).where(*where).offset((page - 1) * size).limit(size)
            )
        ).all()
        total = await self._session.scalar(
            select(func.count()).select_from(ModelConfigModel).where(*where)
        )
        return [*items], total or 0

    async def notification(self, tenant_id: int, item_id: int) -> NotificationModel | None:
        return await self._session.scalar(
            select(NotificationModel).where(
                NotificationModel.tenant_id == tenant_id,
                NotificationModel.id == item_id,
                NotificationModel.delete_time.is_(None),
            )
        )

    async def notifications(
        self, tenant_id: int, page: int, size: int
    ) -> tuple[list[NotificationModel], int]:
        where = (NotificationModel.tenant_id == tenant_id, NotificationModel.delete_time.is_(None))
        items = (
            await self._session.scalars(
                select(NotificationModel).where(*where).offset((page - 1) * size).limit(size)
            )
        ).all()
        total = await self._session.scalar(
            select(func.count()).select_from(NotificationModel).where(*where)
        )
        return [*items], total or 0

    def add(self, item: ModelConfigModel | NotificationModel) -> None:
        self._session.add(item)
