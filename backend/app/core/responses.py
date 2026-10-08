from collections.abc import Mapping
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


class ErrorCode:
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    CSRF_FAILED = "CSRF_FAILED"
    PIN_REQUIRED = "PIN_REQUIRED"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    LIMIT_REACHED = "LIMIT_REACHED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DB_UNAVAILABLE = "DB_UNAVAILABLE"
    HTTP_ERROR = "HTTP_ERROR"


class ApiError(Exception):
    def __init__(
        self,
        status_code,
        message,
        code=ErrorCode.INTERNAL_ERROR,
        fields=None,
        headers: Mapping[str, str] | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.code = code
        self.fields = fields
        self.headers = headers
        super().__init__(message)


class Unauthenticated(ApiError):
    def __init__(self, message="Sign in required"):
        super().__init__(401, message, ErrorCode.UNAUTHENTICATED)


class Forbidden(ApiError):
    def __init__(self, message="Not allowed", code=ErrorCode.FORBIDDEN):
        super().__init__(403, message, code)


class NotFound(ApiError):
    def __init__(self, message="Request not found"):
        super().__init__(404, message, ErrorCode.NOT_FOUND)


def ok(data: Any = None, meta: dict | None = None) -> JSONResponse:
    body = {"success": True}
    if data is not None:
        body["data"] = data
    if meta is not None:
        body["meta"] = meta
    return JSONResponse(content=jsonable_encoder(body))


def failure(
    status_code,
    message,
    code,
    fields=None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = {"success": False, "error": message, "code": code}
    if fields is not None:
        body["fields"] = fields
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return failure(
        exc.status_code,
        exc.message,
        exc.code,
        exc.fields,
        headers=exc.headers,
    )
