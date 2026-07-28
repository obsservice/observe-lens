import json
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from observelens_knowledge_base.common.context import RequestContext, get_request_context
from observelens_knowledge_base.common.dependencies import get_session
from observelens_knowledge_base.common.enums import DocumentStatus, DocumentType
from observelens_knowledge_base.common.exceptions import ValidationDomainError
from observelens_knowledge_base.documents.indexing import SimpleDocumentChunker
from observelens_knowledge_base.documents.repository import DocumentRepository
from observelens_knowledge_base.documents.schemas import (
    CreateDocumentVersionResponse,
    DocumentPage,
    DocumentResponse,
    DocumentVersionResponse,
    IndexTaskResponse,
    UpdateDocumentRequest,
    UploadDocumentResponse,
)
from observelens_knowledge_base.documents.service import DocumentService
from observelens_knowledge_base.documents.storage import DocumentStorage
from observelens_knowledge_base.knowledge_bases.repository import KnowledgeBaseRepository

router = APIRouter(tags=["Document"])


def get_document_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> DocumentService:
    return DocumentService(
        DocumentRepository(session),
        KnowledgeBaseRepository(session),
        DocumentStorage(request.app.state.settings),
        SimpleDocumentChunker(),
        request.app.state.settings,
    )


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=DocumentPage)
async def list_documents(
    knowledge_base_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    keyword: str | None = None,
    document_type: DocumentType | None = None,
    status: DocumentStatus | None = None,
    tag: str | None = None,
) -> DocumentPage:
    return await service.list_documents(
        ctx, knowledge_base_id, page, page_size, keyword, document_type, status, tag
    )


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=UploadDocumentResponse,
    status_code=201,
)
async def upload_document(
    knowledge_base_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form()],
    document_type: Annotated[DocumentType, Form()],
    tags: Annotated[str, Form()] = "[]",
    metadata: Annotated[str, Form()] = "{}",
) -> UploadDocumentResponse:
    return await service.upload(
        ctx,
        knowledge_base_id,
        file,
        name,
        document_type,
        _parse_string_list(tags),
        _parse_object(metadata),
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    return await service.get(ctx, document_id)


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    request: UpdateDocumentRequest,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    return await service.update(ctx, document_id, request)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Response:
    await service.archive(ctx, document_id)
    return Response(status_code=204)


@router.get("/documents/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def list_document_versions(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentVersionResponse]:
    return await service.list_versions(ctx, document_id)


@router.post(
    "/documents/{document_id}/versions",
    response_model=CreateDocumentVersionResponse,
    status_code=201,
)
async def create_document_version(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
    file: Annotated[UploadFile, File()],
    metadata: Annotated[str, Form()] = "{}",
) -> CreateDocumentVersionResponse:
    return await service.create_version(ctx, document_id, file, _parse_object(metadata))


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
    version_id: UUID | None = None,
) -> FileResponse:
    uri = await service.get_content_uri(ctx, document_id, version_id)
    return FileResponse(Path(uri))


@router.post("/documents/{document_id}/reindex", response_model=IndexTaskResponse, status_code=202)
async def reindex_document(
    document_id: UUID,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> IndexTaskResponse:
    return await service.reindex(ctx, document_id)


def _parse_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationDomainError("metadata must be valid JSON object") from exc
    if not isinstance(value, dict):
        raise ValidationDomainError("metadata must be valid JSON object")
    return value


def _parse_string_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationDomainError("tags must be a valid JSON array") from exc
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationDomainError("tags must be a valid JSON string array")
    return value
