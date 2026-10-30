import asyncio
import json
import os
import unittest


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from fastapi import Request
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError as SATimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.responses import ApiError, ErrorCode
from backend.app.main import (
    app,
    database_error_handler,
    db_unavailable_handler,
    health_check,
    http_exception_handler,
    liveness_check,
    root,
)


def response_json(response):
    return json.loads(response.body.decode("utf-8"))


def request(method="GET", path="/test"):
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [(b"host", b"testserver")],
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1),
        }
    )


class MainContractTests(unittest.TestCase):
    def test_root_and_liveness_use_success_envelope(self):
        self.assertEqual(
            response_json(root()),
            {
                "success": True,
                "data": {"message": "Bangla Learning Platform API"},
            },
        )
        self.assertEqual(
            response_json(liveness_check()),
            {"success": True, "data": {"status": "ok"}},
        )

    def test_405_uses_failure_envelope_and_preserves_allow_header(self):
        response = asyncio.run(
            http_exception_handler(
                request(method="POST"),
                StarletteHTTPException(
                    status_code=405,
                    detail="Method Not Allowed",
                    headers={"Allow": "GET, HEAD"},
                ),
            )
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["allow"], "GET, HEAD")
        self.assertEqual(response_json(response)["code"], ErrorCode.METHOD_NOT_ALLOWED)

    def test_404_uses_failure_envelope(self):
        response = asyncio.run(
            http_exception_handler(
                request(path="/missing"),
                StarletteHTTPException(status_code=404, detail="Not Found"),
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response_json(response)["code"], ErrorCode.NOT_FOUND)

    def test_operational_error_is_safe_503(self):
        error = OperationalError("SELECT secret", {}, RuntimeError("db password leaked"))

        response = asyncio.run(db_unavailable_handler(request(), error))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response_json(response),
            {
                "success": False,
                "error": "Database unavailable",
                "code": ErrorCode.DB_UNAVAILABLE,
            },
        )

    def test_nonconnectivity_database_error_is_safe_500(self):
        error = IntegrityError("INSERT secret", {}, RuntimeError("sensitive value"))

        response = asyncio.run(database_error_handler(request(), error))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json(response)["error"], "Internal server error")
        self.assertNotIn("sensitive", response.body.decode("utf-8"))

    def test_pool_timeout_is_safe_503(self):
        response = asyncio.run(
            db_unavailable_handler(request(), SATimeoutError("pool exhausted"))
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response_json(response)["code"], ErrorCode.DB_UNAVAILABLE)

    def test_health_rolls_back_and_returns_503_error(self):
        class BrokenSession:
            def __init__(self):
                self.rollback_calls = 0

            def execute(self, statement):
                raise OperationalError("SELECT 1", {}, RuntimeError("offline"))

            def rollback(self):
                self.rollback_calls += 1

        db = BrokenSession()

        with self.assertRaises(ApiError) as caught:
            health_check(db)

        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.code, ErrorCode.DB_UNAVAILABLE)
        self.assertEqual(db.rollback_calls, 1)

    def test_unhandled_500_keeps_exact_cors_headers_through_asgi_stack(self):
        path = "/__core_test_unhandled_error"

        async def explode():
            raise RuntimeError("sensitive exception text")

        app.add_api_route(path, explode, methods=["GET"], include_in_schema=False)

        async def invoke(origin):
            sent = []
            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("ascii"),
                "query_string": b"",
                "headers": [
                    (b"host", b"testserver"),
                    (b"origin", origin.encode("ascii")),
                ],
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 1),
            }

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                sent.append(message)

            with self.assertRaisesRegex(RuntimeError, "sensitive exception text"):
                await app(scope, receive, send)
            return sent

        allowed = asyncio.run(invoke("http://localhost:5173"))
        denied = asyncio.run(invoke("http://evil.example"))

        self.assertEqual(allowed[0]["status"], 500)
        allowed_headers = dict(allowed[0]["headers"])
        self.assertEqual(
            allowed_headers[b"access-control-allow-origin"],
            b"http://localhost:5173",
        )
        self.assertEqual(
            allowed_headers[b"access-control-allow-credentials"], b"true"
        )
        self.assertEqual(allowed_headers[b"vary"], b"Origin")
        self.assertNotIn(
            "sensitive exception text",
            allowed[1]["body"].decode("utf-8"),
        )

        denied_headers = dict(denied[0]["headers"])
        self.assertNotIn(b"access-control-allow-origin", denied_headers)
        self.assertEqual(denied_headers[b"vary"], b"Origin")


if __name__ == "__main__":
    unittest.main()
