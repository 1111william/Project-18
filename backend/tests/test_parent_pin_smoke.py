import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.responses import ApiError
from backend.app.core.security import hash_password, verify_password
from backend.app.models import Parent
from backend.app.routers.accounts import (
    login,
    request_parent_pin_reset_code,
    reset_parent_pin,
    set_parent_pin,
    verify_parent_pin,
    verify_registration_code,
)
from backend.app.schemas.account_auth import (
    LoginCodeRequest,
    ParentPinRequest,
    ResetParentPinRequest,
    VerifyCodeRequest,
)
from backend.app.services.account_auth import registration_challenges


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

    @patch("backend.app.routers.accounts.send_verification_code", return_value="development")
    @patch("backend.app.services.account_auth.secrets.randbelow", return_value=123456)
    def test_forgotten_pin_can_be_reset_after_email_code_verification(self, _random, _send):
        set_parent_pin(
            ParentPinRequest(pin="4826"),
            parent_id=self.parent.parentID,
            db=self.db,
        )
        response = request_parent_pin_reset_code(parent_id=self.parent.parentID, db=self.db)
        payload = json.loads(response.body)["data"]
        challenge_id = payload["challenge_id"]

        verified = verify_registration_code(
            VerifyCodeRequest(challenge_id=challenge_id, code="123456"),
            request=SimpleNamespace(session={}),
            db=self.db,
        )
        self.assertTrue(json.loads(verified.body)["data"]["pin_reset"])

        request = SimpleNamespace(
            session={"pinVerified": True, "pinAttempts": 4, "pinLockedUntil": 9999999999}
        )
        reset_parent_pin(
            ResetParentPinRequest(challenge_id=challenge_id, new_pin="1357"),
            request=request,
            parent_id=self.parent.parentID,
            db=self.db,
        )
        self.db.refresh(self.parent)

        self.assertFalse(verify_password("4826", self.parent.pinHash))
        self.assertTrue(verify_password("1357", self.parent.pinHash))
        self.assertFalse(request.session["pinVerified"])
        self.assertEqual(request.session["pinAttempts"], 0)
        self.assertNotIn("pinLockedUntil", request.session)
        with self.assertRaises(ApiError):
            registration_challenges.get_authorized_pin_reset(challenge_id)


if __name__ == "__main__":
    unittest.main()
