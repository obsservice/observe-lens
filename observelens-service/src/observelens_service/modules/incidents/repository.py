import builtins

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_service.modules.incidents.models import IncidentIntegrationModel, IncidentModel


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, tenant_id: int, page: int, page_size: int, severity: str | None, status: str | None
    ) -> tuple[list[IncidentModel], int]:
        filters = [IncidentModel.tenant_id == tenant_id, IncidentModel.delete_time.is_(None)]
        if severity:
            filters.append(IncidentModel.severity == severity)
        if status:
            filters.append(IncidentModel.status == status)
        query: Select[tuple[IncidentModel]] = (
            select(IncidentModel).where(*filters).order_by(IncidentModel.update_time.desc())
        )
        items = (
            await self._session.scalars(query.offset((page - 1) * page_size).limit(page_size))
        ).all()
        total = await self._session.scalar(
            select(func.count()).select_from(IncidentModel).where(*filters)
        )
        return list(items), total or 0

    async def get(self, tenant_id: int, incident_id: int) -> IncidentModel | None:
        result = await self._session.scalar(
            select(IncidentModel).where(
                IncidentModel.tenant_id == tenant_id,
                IncidentModel.id == incident_id,
                IncidentModel.delete_time.is_(None),
            )
        )
        return result

    async def get_integration(
        self, tenant_id: int, integration_id: int
    ) -> IncidentIntegrationModel | None:
        result = await self._session.scalar(
            select(IncidentIntegrationModel).where(
                IncidentIntegrationModel.tenant_id == tenant_id,
                IncidentIntegrationModel.id == integration_id,
                IncidentIntegrationModel.delete_time.is_(None),
            )
        )
        return result

    async def list_integrations(self, tenant_id: int) -> builtins.list[IncidentIntegrationModel]:
        result = await self._session.scalars(
            select(IncidentIntegrationModel)
            .where(
                IncidentIntegrationModel.tenant_id == tenant_id,
                IncidentIntegrationModel.delete_time.is_(None),
            )
            .order_by(IncidentIntegrationModel.create_time.desc())
        )
        return [*result.all()]

    def add(self, model: IncidentModel | IncidentIntegrationModel) -> None:
        self._session.add(model)
