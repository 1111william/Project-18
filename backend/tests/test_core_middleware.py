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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.responses import ApiError, ErrorCode
from backend.app.database import Base
from backend.app.middleware import (
    current_parent_id,
    owned_child,
    require_admin,
    require_pin,
)
from backend.app.models import ChildProfile, Parent


def request(session):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1),
            "session": session,
        }
    )


class DatabaseGuardTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.db.add_all(
            [
                Parent(
                    parentID=1,
                    email="parent@example.com",
                    passwordHash="hash",
                    displayName="Parent",
                    isAdmin=False,
                ),
                Parent(
                    parentID=2,
                    email="admin@example.com",
                    passwordHash="hash",
                    displayName="Admin",
                    isAdmin=True,
                ),
            ]
        )
        self.db.add(
            ChildProfile(
                childID=1,
                parentID=1,
                nickname="Child",
                ageBand="junior",
            )
        )
        self.db.add(
            ChildProfile(
                childID=2,
                parentID=2,
                nickname="Admin Child",
                ageBand="junior",
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def assert_api_status(self, status, callback):
        with self.assertRaises(ApiError) as caught:
            callback()
        self.assertEqual(caught.exception.status_code, status)
        return caught.exception

    def test_parent_id_is_checked_against_database(self):
        self.assertEqual(current_parent_id(request({"parentID": "1"}), self.db), 1)
        for invalid_parent_id in ("not-an-int", 1.0, 1.5, True, " 1", "+1"):
            with self.subTest(parent_id=invalid_parent_id):
                self.assert_api_status(
                    401,
                    lambda value=invalid_parent_id: current_parent_id(
                        request({"parentID": value}), self.db
                    ),
                )
        self.assert_api_status(
            401,
            lambda: current_parent_id(request({"parentID": 999}), self.db),
        )

    def test_missing_session_middleware_returns_401(self):
        bare_request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": "/",
                "raw_path": b"/",
                "query_string": b"",
                "headers": [],
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 1),
            }
        )
        error = self.assert_api_status(
            401,
            lambda: current_parent_id(bare_request, self.db),
        )
        self.assertEqual(error.code, ErrorCode.UNAUTHENTICATED)

    def test_admin_status_comes_from_database_not_cookie(self):
        self.assert_api_status(
            403,
            lambda: require_admin(
                request({"parentID": 1, "isAdmin": True}), self.db
            ),
        )
        self.assertEqual(
            require_admin(request({"parentID": 2, "isAdmin": False}), self.db),
            2,
        )

    def test_child_ownership_uses_database_admin_flag(self):
        self.assert_api_status(
            403,
            lambda: owned_child(
                childID=2,
                request=request({"parentID": 1, "isAdmin": True}),
                db=self.db,
            ),
        )
        child = owned_child(
            childID=1,
            request=request({"parentID": 2, "isAdmin": False}),
            db=self.db,
        )
        self.assertEqual(child.childID, 1)

    def test_missing_child_is_404(self):
        self.assert_api_status(
            404,
            lambda: owned_child(
                childID=999,
                request=request({"parentID": 1}),
                db=self.db,
            ),
        )

    def test_pin_semantics_are_unchanged(self):
        for unverified in (None, False, 1, "true", "1"):
            with self.subTest(pin_verified=unverified):
                session = {"parentID": 1}
                if unverified is not None:
                    session["pinVerified"] = unverified
                error = self.assert_api_status(
                    403,
                    lambda value=session: require_pin(request(value), self.db),
                )
                self.assertEqual(error.code, ErrorCode.PIN_REQUIRED)
        self.assertIsNone(
            require_pin(request({"parentID": 1, "pinVerified": True}), self.db)
        )


if __name__ == "__main__":
    unittest.main()
