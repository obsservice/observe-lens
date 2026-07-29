from typing import Never

from fastapi import Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


class ResourceNotFoundError(DomainError):
    def __init__(self, resource: str) -> None:
        super().__init__("RESOURCE_NOT_FOUND", f"{resource} not found", 404)


class ResourceConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("RESOURCE_CONFLICT", message, 409)


class ResourceAlreadyExistsError(DomainError):
    def __init__(self, resource: str, field: str, value: str) -> None:
        message = f'{resource} with {field} "{value}" already exists'
        super().__init__("RESOURCE_ALREADY_EXISTS", message, 409)


class InvalidRequestError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_REQUEST", message, 400)


class DependencyUnavailableError(DomainError):
    def __init__(self, dependency: str) -> None:
        super().__init__("DEPENDENCY_UNAVAILABLE", f"{dependency} is unavailable", 503)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    request_id = request.headers.get("x-request-id", "")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "request_id": request_id, "details": {}},
    )


def unreachable() -> Never:
    raise RuntimeError("Unreachable")
