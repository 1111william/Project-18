import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.responses import ApiError
from backend.app.core.security import hash_password, verify_password
from backend.app.models import Parent
from backend.app.routers.accounts import login, set_parent_pin, verify_parent_pin
from backend.app.schemas.account_auth import LoginCodeRequest, ParentPinRequest


class ParentPinSmokeTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Parent.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.parent = Parent(
            email="parent@example.test",
            passwordHash=hash_password("correct-password"),
            displayName="Test Parent",
        )
        self.db.add(self.parent)
        self.db.commit()
        self.db.refresh(self.parent)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_pin_is_hashed_and_cannot_be_overwritten(self):
        set_parent_pin(
            ParentPinRequest(pin="4826"),
            parent_id=self.parent.parentID,
            db=self.db,
        )
        self.db.refresh(self.parent)
        self.assertNotEqual(self.parent.pinHash, "4826")
        self.assertTrue(verify_password("4826", self.parent.pinHash))

        with self.assertRaises(ApiError) as raised:
            set_parent_pin(
                ParentPinRequest(pin="1357"),
                parent_id=self.parent.parentID,
                db=self.db,
            )
        self.assertEqual(raised.exception.status_code, 409)

    def test_password_login_creates_session_without_email_challenge(self):
        request = SimpleNamespace(session={"stale": True})

        response = login(
            LoginCodeRequest(
                email="parent@example.test",
                password="correct-password",
            ),
            request=request,
            db=self.db,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.session["parentID"], self.parent.parentID)
        self.assertFalse(request.session["pinVerified"])
        self.assertNotIn("stale", request.session)
        self.assertNotIn("challenge_id", response.body.decode("utf-8"))

    def test_pin_verification_sets_session_and_limits_attempts(self):
        set_parent_pin(
            ParentPinRequest(pin="4826"),
            parent_id=self.parent.parentID,
            db=self.db,
        )
        request = SimpleNamespace(session={})

        for attempt in range(5):
            with self.assertRaises(ApiError) as raised:
                verify_parent_pin(
                    ParentPinRequest(pin="0000"),
                    request=request,
                    parent_id=self.parent.parentID,
                    db=self.db,
                )
            self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("pinLockedUntil", request.session)

        verified_request = SimpleNamespace(session={})
        verify_parent_pin(
            ParentPinRequest(pin="4826"),
            request=verified_request,
            parent_id=self.parent.parentID,
            db=self.db,
        )
        self.assertTrue(verified_request.session["pinVerified"])


if __name__ == "__main__":
    unittest.main()
