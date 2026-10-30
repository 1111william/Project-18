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

from starlette.requests import Request

from backend.app.core.security import (
    SessionCSRFMiddleware,
    hash_password,
    request_origin_is_trusted,
    verify_password,
)


def request(headers=None, method="POST", host="api.example.com"):
    encoded_headers = [(b"host", host.encode("ascii"))]
    for name, value in (headers or {}).items():
        encoded_headers.append((name.lower().encode("ascii"), value.encode("ascii")))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": "/api/children",
            "raw_path": b"/api/children",
            "query_string": b"",
            "headers": encoded_headers,
            "server": (host, 443),
            "client": ("127.0.0.1", 1234),
        }
    )


class PasswordTests(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        hashed = hash_password("correct horse battery staple")

        self.assertTrue(verify_password("correct horse battery staple", hashed))
        self.assertFalse(verify_password("wrong", hashed))
        self.assertFalse(verify_password("correct horse battery staple", "not-a-bcrypt-hash"))

    def test_passwords_over_72_utf8_bytes_are_explicitly_rejected(self):
        for password in ("x" * 73, "😀" * 19):
            with self.subTest(byte_length=len(password.encode("utf-8"))):
                with self.assertRaisesRegex(ValueError, "72 UTF-8 bytes"):
                    hash_password(password)
                with self.assertRaisesRegex(ValueError, "72 UTF-8 bytes"):
                    verify_password(password, "$2b$12$invalid")


class CsrfTests(unittest.TestCase):
    def test_exact_allowed_origin_and_referer_are_trusted(self):
        allowed = {"https://app.example.com"}

        self.assertTrue(
            request_origin_is_trusted(
                request({"Origin": "https://app.example.com"}), allowed
            )
        )
        self.assertTrue(
            request_origin_is_trusted(
                request({"Referer": "https://app.example.com/children/1"}), allowed
            )
        )

    def test_missing_malformed_or_lookalike_origin_is_rejected(self):
        allowed = {"https://app.example.com"}

        self.assertFalse(request_origin_is_trusted(request(), allowed))
        self.assertFalse(
            request_origin_is_trusted(request({"Origin": "null"}), allowed)
        )
        self.assertFalse(
            request_origin_is_trusted(
                request({"Origin": "https://app.example.com.evil.test"}), allowed
            )
        )
        self.assertFalse(
            request_origin_is_trusted(request({"Origin": "https://[bad"}), allowed)
        )
        self.assertFalse(
            request_origin_is_trusted(request({"Referer": "https://[bad"}), allowed)
        )

    def test_same_api_origin_is_trusted(self):
        self.assertTrue(
            request_origin_is_trusted(
                request({"Origin": "https://api.example.com"}), set()
            )
        )

    def test_middleware_blocks_only_session_cookie_writes(self):
        async def downstream(scope, receive, send):
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = SessionCSRFMiddleware(
            downstream,
            allowed_origins=["https://app.example.com"],
            session_cookie="session",
        )

        async def invoke(headers, method="POST"):
            sent = []
            req = request(headers, method=method)

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                sent.append(message)

            await middleware(req.scope, receive, send)
            return sent

        blocked = asyncio.run(invoke({"Cookie": "session=signed-value"}))
        allowed = asyncio.run(
            invoke(
                {
                    "Cookie": "session=signed-value",
                    "Origin": "https://app.example.com",
                }
            )
        )
        anonymous = asyncio.run(invoke({}))
        safe_method = asyncio.run(
            invoke({"Cookie": "session=signed-value"}, method="GET")
        )

        self.assertEqual(blocked[0]["status"], 403)
        blocked_body = json.loads(blocked[1]["body"])
        self.assertEqual(blocked_body["code"], "CSRF_FAILED")
        self.assertEqual(allowed[0]["status"], 204)
        self.assertEqual(anonymous[0]["status"], 204)
        self.assertEqual(safe_method[0]["status"], 204)


if __name__ == "__main__":
    unittest.main()
