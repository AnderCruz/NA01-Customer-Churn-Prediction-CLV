"""Stable and sanitised error responses for the API."""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from starlette.responses import JSONResponse


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_ERRORS = {
    ErrorCode.INVALID_REQUEST: (400, "The request is invalid."),
    ErrorCode.AUTH_REQUIRED: (401, "Authentication is required."),
    ErrorCode.FORBIDDEN: (403, "This operation is not permitted."),
    ErrorCode.NOT_FOUND: (404, "The resource was not found."),
    ErrorCode.METHOD_NOT_ALLOWED: (405, "This method is not allowed."),
    ErrorCode.VALIDATION_ERROR: (422, "The request parameters are invalid."),
    ErrorCode.SERVICE_UNAVAILABLE: (503, "The service is not ready."),
    ErrorCode.EVIDENCE_UNAVAILABLE: (503, "Research evidence is unavailable."),
    ErrorCode.INTERNAL_ERROR: (500, "An internal error occurred."),
}
_HTTP_CODES = {
    status: code
    for code, (status, _) in _ERRORS.items()
    if code is not ErrorCode.EVIDENCE_UNAVAILABLE
}


class ApiFailure(Exception):
    """An expected API failure identified by a reviewed public code."""

    def __init__(self, code: ErrorCode) -> None:
        self.code = code
        super().__init__(code.value)


class ApiError(BaseModel):
    """The v1 error envelope, without optional request issue details."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    request_id: UUID
    code: ErrorCode
    message: str


def http_error_code(status_code: int) -> ErrorCode:
    return _HTTP_CODES.get(status_code, ErrorCode.INTERNAL_ERROR)


def error_response(code: ErrorCode, request_id: UUID) -> JSONResponse:
    status, message = _ERRORS[code]
    headers: dict[str, str] = {}
    if code is ErrorCode.AUTH_REQUIRED:
        headers["WWW-Authenticate"] = "Bearer"
    elif code is ErrorCode.METHOD_NOT_ALLOWED:
        headers["Allow"] = "GET"
    payload = ApiError(request_id=request_id, code=code, message=message)
    return JSONResponse(payload.model_dump(mode="json"), status_code=status, headers=headers)
