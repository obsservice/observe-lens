from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from observelens_service.clients.knowledge_base import KnowledgeBaseClient
from observelens_service.config.settings import get_settings
from observelens_service.modules.knowledge.schemas import (
    KnowledgeFilePage,
    KnowledgeFileResponse,
    KnowledgeFileStatusResponse,
)
from observelens_service.modules.knowledge.service import KnowledgeService

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


def get_service() -> KnowledgeService:
    settings = get_settings()
    return KnowledgeService(
        KnowledgeBaseClient(
            str(settings.knowledge_base_url) if settings.knowledge_base_url else None,
            settings.knowledge_base_timeout_seconds,
        )
    )


ServiceDependency = Annotated[KnowledgeService, Depends(get_service)]


@router.get("/files", response_model=KnowledgeFilePage)
async def list_files(
    service: ServiceDependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    file_type: str | None = None,
) -> KnowledgeFilePage:
    return await service.list_files(page, page_size, keyword, file_type)


@router.post("/files", response_model=KnowledgeFileResponse, status_code=201)
async def upload_file(
    service: ServiceDependency, file: Annotated[UploadFile, File()]
) -> KnowledgeFileResponse:
    content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 50 MiB limit")
    file_name = Path(file.filename or "upload").name
    if not file_name:
        raise HTTPException(status_code=422, detail="File name is required")
    return await service.upload(file_name, file.content_type or "application/octet-stream", content)


@router.get("/file-types")
async def list_file_types(service: ServiceDependency) -> list[dict[str, str]]:
    return await service.file_types()


@router.get("/index-statuses")
async def list_index_statuses(service: ServiceDependency) -> list[dict[str, str]]:
    return await service.index_statuses()


@router.get("/files/{file_id}", response_model=KnowledgeFileResponse)
async def get_file(file_id: str, service: ServiceDependency) -> KnowledgeFileResponse:
    return await service.get_file(file_id)


@router.delete("/files/{file_id}", status_code=204)
async def delete_file(file_id: str, service: ServiceDependency) -> Response:
    await service.delete(file_id)
    return Response(status_code=204)


@router.get("/files/{file_id}/status", response_model=KnowledgeFileStatusResponse)
async def get_file_status(file_id: str, service: ServiceDependency) -> KnowledgeFileStatusResponse:
    return await service.status(file_id)


@router.post(
    "/files/{file_id}/reindex", response_model=KnowledgeFileStatusResponse, status_code=202
)
async def reindex_file(file_id: str, service: ServiceDependency) -> KnowledgeFileStatusResponse:
    return await service.reindex(file_id)
