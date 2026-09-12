import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, api_error_handler, failure, ok
from backend.app.database import get_db
from backend.app.routers import children, quizzes

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
)

app = FastAPI(
    title="Bangla Learning Platform API",
    version="0.1.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="session",
    max_age=86400,
    same_site="none" if settings.CROSS_SITE_COOKIE == "1" else "lax",
    https_only=settings.CROSS_SITE_COOKIE == "1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.add_exception_handler(ApiError, api_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    fields = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
        if location:
            fields.append(".".join(location))
    return failure(400, "Invalid input", ErrorCode.VALIDATION_FAILED, fields or None)


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logging.getLogger("api").exception("Unhandled exception on %s %s", request.method, request.url.path)
    detail = str(exc) if settings.DEBUG == "1" else "Internal server error"
    return failure(500, detail, ErrorCode.INTERNAL_ERROR)


app.include_router(
    quizzes.router,
    prefix="/api/quizzes",
    tags=["Quiz"]
)

app.include_router(
    children.router,
    prefix="/api/children",
    tags=["Children"]
)


@app.get("/")
def root():
    return {
        "message": "Bangla Learning Platform API"
    }


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ApiError(503, "Database unreachable", ErrorCode.DB_UNAVAILABLE) from exc
    return ok({"status": "ok", "database": "up"})
