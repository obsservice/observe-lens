from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundError(DomainError):
    def __init__(self, code: str, resource: str) -> None:
        super().__init__(code, f"{resource} not found", 404)


class PermissionDeniedError(DomainError):
    def __init__(self) -> None:
        super().__init__("PERMISSION_DENIED", "Permission denied", 403)


class ValidationDomainError(DomainError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("VALIDATION_FAILED", message, 400, details)


class UnsupportedDocumentTypeError(DomainError):
    def __init__(self, mime_type: str) -> None:
        super().__init__(
            "DOCUMENT_TYPE_UNSUPPORTED",
            f"Document type is unsupported: {mime_type}",
            400,
            {"mime_type": mime_type},
        )


class ConflictError(DomainError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, 409)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    trace_id = request.headers.get("x-request-id", "")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "trace_id": trace_id,
            }
        },
    )
