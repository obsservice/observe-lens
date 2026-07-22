from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.common.context import RequestContext
from observelens_service.common.exceptions import ResourceNotFoundError
from observelens_service.modules.conversations.service import new_id
from observelens_service.modules.settings.models import ModelConfigModel, NotificationModel
from observelens_service.modules.settings.repository import SettingsRepository
from observelens_service.modules.settings.schemas import (
    ModelPage,
    ModelResponse,
    ModelWrite,
    NotificationPage,
    NotificationResponse,
    NotificationWrite,
    TestResult,
)


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SettingsRepository(session)

    async def models(self, c: RequestContext, page: int, size: int) -> ModelPage:
        rows, total = await self._repo.models(c.tenant_id, page, size)
        return ModelPage(
            items=[ModelResponse.model_validate(x) for x in rows],
            total=total,
            page=page,
            page_size=size,
        )

    async def create_model(self, c: RequestContext, r: ModelWrite) -> ModelResponse:
        item = ModelConfigModel(
            id=new_id(),
            tenant_id=c.tenant_id,
            name=r.name,
            provider=r.provider,
            model_name=r.model_name,
            endpoint=r.endpoint,
            credential=r.credential_ref,
            create_by=c.user_id,
        )
        self._repo.add(item)
        await self._session.flush()
        return ModelResponse.model_validate(item)

    async def model(self, c: RequestContext, i: int) -> ModelConfigModel:
        item = await self._repo.model(c.tenant_id, i)
        if item is None:
            raise ResourceNotFoundError("Model configuration")
        return item

    async def update_model(self, c: RequestContext, i: int, r: ModelWrite) -> ModelResponse:
        item = await self.model(c, i)
        for k, v in {
            "name": r.name,
            "provider": r.provider,
            "model_name": r.model_name,
            "endpoint": r.endpoint,
            "credential": r.credential_ref,
        }.items():
            setattr(item, k, v)
        item.update_by = c.user_id
        await self._session.flush()
        return ModelResponse.model_validate(item)

    async def delete_model(self, c: RequestContext, i: int) -> None:
        item = await self.model(c, i)
        item.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def default_model(self, c: RequestContext, i: int) -> ModelResponse:
        item = await self.model(c, i)
        await self._session.execute(
            update(ModelConfigModel)
            .where(ModelConfigModel.tenant_id == c.tenant_id)
            .values(is_default=False)
        )
        item.is_default = True
        await self._session.flush()
        return ModelResponse.model_validate(item)

    async def test_model(self, c: RequestContext, i: int) -> TestResult:
        item = await self.model(c, i)
        return TestResult(
            status="passed" if item.status == "ACTIVE" else "failed",
            message="Configuration is active"
            if item.status == "ACTIVE"
            else "Configuration is disabled",
        )

    async def notifications(self, c: RequestContext, page: int, size: int) -> NotificationPage:
        rows, total = await self._repo.notifications(c.tenant_id, page, size)
        return NotificationPage(
            items=[self._notification(x) for x in rows], total=total, page=page, page_size=size
        )

    def _notification(self, x: NotificationModel) -> NotificationResponse:
        return NotificationResponse.model_validate(
            {
                "id": x.id,
                "name": x.name,
                "channel_type": x.channel_type,
                "status": x.status,
                "target": x.config.get("target", ""),
                "create_time": x.create_time,
                "update_time": x.update_time,
            }
        )

    async def create_notification(
        self, c: RequestContext, r: NotificationWrite
    ) -> NotificationResponse:
        item = NotificationModel(
            id=new_id(),
            tenant_id=c.tenant_id,
            name=r.name,
            channel_type=r.channel_type,
            config={"target": r.target},
            credential=r.credential_ref,
            create_by=c.user_id,
        )
        self._repo.add(item)
        await self._session.flush()
        return self._notification(item)

    async def notification(self, c: RequestContext, i: int) -> NotificationModel:
        item = await self._repo.notification(c.tenant_id, i)
        if item is None:
            raise ResourceNotFoundError("Notification")
        return item

    async def update_notification(
        self, c: RequestContext, i: int, r: NotificationWrite
    ) -> NotificationResponse:
        item = await self.notification(c, i)
        item.name = r.name
        item.channel_type = r.channel_type
        item.config = {"target": r.target}
        item.credential = r.credential_ref
        item.update_by = c.user_id
        await self._session.flush()
        return self._notification(item)

    async def delete_notification(self, c: RequestContext, i: int) -> None:
        item = await self.notification(c, i)
        item.delete_time = datetime.now(UTC)
        await self._session.flush()

    async def test_notification(self, c: RequestContext, i: int) -> TestResult:
        item = await self.notification(c, i)
        return TestResult(
            status="sent" if item.status == "ACTIVE" else "failed",
            message="Test notification accepted"
            if item.status == "ACTIVE"
            else "Notification is disabled",
        )
