from urllib.parse import urlsplit

import bcrypt
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.app.config import normalise_origin
from backend.app.core.responses import ErrorCode, failure


BCRYPT_MAX_PASSWORD_BYTES = 72
SAFE_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}


def _password_bytes(plain: str) -> bytes:
    if not isinstance(plain, str):
        raise TypeError("Password must be a string")
    encoded = plain.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password must not exceed 72 UTF-8 bytes for bcrypt")
    return encoded


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_password_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    encoded = _password_bytes(plain)
    try:
        return bcrypt.checkpw(encoded, hashed.encode("utf-8"))
    except (AttributeError, UnicodeError, ValueError):
        return False


def _referer_origin(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
    except ValueError as exc:
        raise RuntimeError("Invalid Referer origin") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("Invalid Referer origin")
    return normalise_origin(f"{parsed.scheme}://{parsed.netloc}")


def request_write_origin(request: Request) -> str | None:
    """Return a validated Origin, with Referer as a browser-compatible fallback."""

    origin = request.headers.get("origin")
    if origin:
        try:
            return normalise_origin(origin)
        except RuntimeError:
            return None
    referer = request.headers.get("referer")
    if referer:
        try:
            return _referer_origin(referer)
        except RuntimeError:
            return None
    return None


def request_origin_is_trusted(request: Request, allowed_origins: set[str]) -> bool:
    supplied_origin = request_write_origin(request)
    if supplied_origin is None:
        return False
    try:
        request_origin = normalise_origin(
            f"{request.url.scheme}://{request.url.netloc}"
        )
    except RuntimeError:
        request_origin = None
    return supplied_origin == request_origin or supplied_origin in allowed_origins


class SessionCSRFMiddleware:
    """Require an exact trusted Origin/Referer for session-cookie writes.

    This protects browser requests carrying the signed session cookie. It does
    not create server-side session revocation; future authentication work must
    still clear cookies and define logout/session lifecycle semantics.
    """

    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: list[str],
        session_cookie: str,
    ) -> None:
        self.app = app
        self.allowed_origins = set(allowed_origins)
        self.session_cookie = session_cookie

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"].upper() in SAFE_HTTP_METHODS:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        has_session_cookie = self.session_cookie in request.cookies
        if has_session_cookie and not request_origin_is_trusted(
            request, self.allowed_origins
        ):
            response = failure(
                403,
                "Trusted Origin or Referer required for session write",
                ErrorCode.CSRF_FAILED,
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
