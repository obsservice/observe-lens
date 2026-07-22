from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observelens_service.common.context import RequestContext
from observelens_service.common.dependencies import get_request_context, get_session_factory
from observelens_service.database.session import session_scope
from observelens_service.modules.settings.schemas import (
    ModelPage,
    ModelResponse,
    ModelWrite,
    NotificationPage,
    NotificationResponse,
    NotificationWrite,
    TestResult,
)
from observelens_service.modules.settings.service import SettingsService

router = APIRouter(tags=["Settings"])


async def get_service(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[SettingsService]:
    async with session_scope(factory) as s:
        yield SettingsService(s)


S = Annotated[SettingsService, Depends(get_service)]
C = Annotated[RequestContext, Depends(get_request_context)]


@router.get("/models", response_model=ModelPage)
async def list_models(
    c: C, s: S, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)
) -> ModelPage:
    return await s.models(c, page, page_size)


@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(r: ModelWrite, c: C, s: S) -> ModelResponse:
    return await s.create_model(c, r)


@router.get("/models/providers")
async def providers() -> list[dict[str, str]]:
    return [
        {"value": x, "label": x}
        for x in ("OPENAI", "AZURE_OPENAI", "QWEN", "DEEPSEEK", "CLAUDE", "GEMINI")
    ]


@router.get("/models/statuses")
async def model_statuses() -> list[dict[str, str]]:
    return [{"value": x, "label": x.title()} for x in ("ACTIVE", "DISABLED")]


@router.get("/models/{item_id:int}", response_model=ModelResponse)
async def get_model(item_id: int, c: C, s: S) -> ModelResponse:
    return ModelResponse.model_validate(await s.model(c, item_id))


@router.put("/models/{item_id:int}", response_model=ModelResponse)
async def update_model(item_id: int, r: ModelWrite, c: C, s: S) -> ModelResponse:
    return await s.update_model(c, item_id, r)


@router.delete("/models/{item_id:int}", status_code=204)
async def delete_model(item_id: int, c: C, s: S) -> Response:
    await s.delete_model(c, item_id)
    return Response(status_code=204)


@router.post("/models/{item_id:int}/test", response_model=TestResult)
async def test_model(item_id: int, c: C, s: S) -> TestResult:
    return await s.test_model(c, item_id)


@router.post("/models/{item_id:int}/set-default", response_model=ModelResponse)
async def set_default(item_id: int, c: C, s: S) -> ModelResponse:
    return await s.default_model(c, item_id)


@router.get("/notifications", response_model=NotificationPage)
async def list_notifications(
    c: C, s: S, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)
) -> NotificationPage:
    return await s.notifications(c, page, page_size)


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(r: NotificationWrite, c: C, s: S) -> NotificationResponse:
    return await s.create_notification(c, r)


@router.get("/notifications/types")
async def notification_types() -> list[dict[str, str]]:
    return [{"value": "WEBHOOK", "label": "Webhook"}]


@router.get("/notifications/statuses")
async def notification_statuses() -> list[dict[str, str]]:
    return [{"value": x, "label": x.title()} for x in ("ACTIVE", "DISABLED")]


@router.get("/notifications/{item_id:int}", response_model=NotificationResponse)
async def get_notification(item_id: int, c: C, s: S) -> NotificationResponse:
    return s._notification(await s.notification(c, item_id))


@router.put("/notifications/{item_id:int}", response_model=NotificationResponse)
async def update_notification(
    item_id: int, r: NotificationWrite, c: C, s: S
) -> NotificationResponse:
    return await s.update_notification(c, item_id, r)


@router.delete("/notifications/{item_id:int}", status_code=204)
async def delete_notification(item_id: int, c: C, s: S) -> Response:
    await s.delete_notification(c, item_id)
    return Response(status_code=204)


@router.post("/notifications/{item_id:int}/test", response_model=TestResult)
async def test_notification(item_id: int, c: C, s: S) -> TestResult:
    return await s.test_notification(c, item_id)
