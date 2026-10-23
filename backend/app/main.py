import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import (
    DBAPIError,
    DisconnectionError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError as SQLAlchemyTimeoutError,
)
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from backend.app.config import settings
from backend.app.core.responses import (
    ApiError,
    ErrorCode,
    api_error_handler,
    failure,
    ok,
)
from backend.app.core.security import SessionCSRFMiddleware
from backend.app.database import get_db
from backend.app.routers import accounts, children, quizzes


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("api")

settings.validate_for_startup()

app = FastAPI(
    title="Bangla Learning Platform API",
    version="0.1.0",
)

# Middleware is wrapped in reverse registration order. CORS is deliberately
# outermost so even CSRF failures carry the correct browser CORS headers.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
    same_site=settings.SESSION_COOKIE_SAMESITE,
    https_only=settings.SESSION_COOKIE_SECURE,
)
app.add_middleware(
    SessionCSRFMiddleware,
    allowed_origins=settings.allowed_origins,
    session_cookie=settings.SESSION_COOKIE_NAME,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)

app.add_exception_handler(ApiError, api_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    fields: list[str] = []
    for error in exc.errors():
        location = [
            str(part)
            for part in error["loc"]
            if part not in ("body", "query", "path")
        ]
        if location:
            field = ".".join(location)
            if field not in fields:
                fields.append(field)
    return failure(400, "Invalid input", ErrorCode.VALIDATION_FAILED, fields or None)


def _http_error_code(status_code: int) -> str:
    return {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHENTICATED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
    }.get(status_code, ErrorCode.HTTP_ERROR)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        message = "Route not found"
    elif exc.status_code == 405:
        message = "Method not allowed"
    elif exc.status_code >= 500:
        message = "Internal server error"
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = "HTTP request failed"
    return failure(
        exc.status_code,
        message,
        _http_error_code(exc.status_code),
        headers=exc.headers,
    )


async def db_unavailable_handler(request: Request, exc: Exception):
    logger.error(
        "Database unavailable on %s %s (%s)",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return failure(503, "Database unavailable", ErrorCode.DB_UNAVAILABLE)


app.add_exception_handler(OperationalError, db_unavailable_handler)
app.add_exception_handler(DisconnectionError, db_unavailable_handler)
app.add_exception_handler(SQLAlchemyTimeoutError, db_unavailable_handler)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    if isinstance(exc, DBAPIError) and exc.connection_invalidated:
        return await db_unavailable_handler(request, exc)
    logger.error(
        "Database operation failed on %s %s (%s)",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return failure(500, "Internal server error", ErrorCode.INTERNAL_ERROR)


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    detail = str(exc) if settings.DEBUG else "Internal server error"
    # Starlette runs the generic Exception handler from ServerErrorMiddleware,
    # which is outside every user middleware (including CORSMiddleware). Add
    # the narrowly scoped CORS headers here so browser clients can still read
    # the safe error envelope. Never reflect an unconfigured Origin.
    origin = request.headers.get("origin")
    cors_headers = {"Vary": "Origin"}
    if origin in settings.allowed_origins:
        cors_headers.update(
            {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        )
    return failure(
        500,
        detail,
        ErrorCode.INTERNAL_ERROR,
        headers=cors_headers,
    )


app.include_router(
    quizzes.router,
    prefix="/api/quizzes",
    tags=["Quiz"],
)
app.include_router(
    children.router,
    prefix="/api/children",
    tags=["Children"],
)

app.include_router(
    accounts.router,
    prefix="/api/auth",
    tags=["Account"]
)


@app.get("/")
def root():
    return ok({"message": "Bangla Learning Platform API"})


@app.get("/api/live")
def liveness_check():
    return ok({"status": "ok"})


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.rollback()
        raise ApiError(
            503,
            "Database unavailable",
            ErrorCode.DB_UNAVAILABLE,
        ) from exc
    return ok({"status": "ok", "database": "up"})
