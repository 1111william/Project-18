import json
import os
import unittest
from unittest.mock import patch


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode
from backend.app.database import Base
from backend.app.models import ChildProfile, LearningLevel, Parent
from backend.app.routers.children import (
    create_child,
    list_children,
    update_child,
)
from backend.app.schemas.child import ChildCreate, ChildUpdate


def response_json(response):
    return json.loads(response.body.decode("utf-8"))


class ChildSchemaTests(unittest.TestCase):
    def test_nickname_is_trimmed_before_length_validation(self):
        body = ChildCreate(nickname=f"  {'x' * 60}  ")

        self.assertEqual(body.nickname, "x" * 60)

    def test_blank_or_null_nickname_is_rejected(self):
        for payload in ({"nickname": "   "}, {"nickname": None}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError):
                    ChildCreate(**payload)

    def test_update_nonnullable_fields_reject_explicit_null(self):
        for payload in ({"nickname": None}, {"ageBand": None}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError):
                    ChildUpdate(**payload)

    def test_update_omission_and_nullable_avatar_are_distinguishable(self):
        omitted = ChildUpdate()
        explicit_null = ChildUpdate(avatar=None)

        self.assertNotIn("avatar", omitted.model_fields_set)
        self.assertIn("avatar", explicit_null.model_fields_set)


class ChildRouterTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.db.add(
            Parent(
                parentID=1,
                email="parent@example.com",
                passwordHash="hash",
                displayName="Parent",
                isAdmin=False,
            )
        )
        self.db.add(
            LearningLevel(
                levelID=1,
                levelOrder=1,
                title="Beginner",
                passMark=70,
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_create_list_and_clear_avatar(self):
        response = create_child(
            ChildCreate(nickname="  Rafi  ", avatar="avatar.png"),
            parent_id=1,
            db=self.db,
        )
        child_id = response_json(response)["data"]["childID"]
        child = self.db.get(ChildProfile, child_id)

        self.assertEqual(child.nickname, "Rafi")
        self.assertEqual(child.currentLevelID, 1)
        listed = response_json(list_children(parent_id=1, db=self.db))["data"]
        self.assertEqual([row["childID"] for row in listed], [child_id])

        update_child(ChildUpdate(avatar=None), child=child, db=self.db)
        self.db.expire_all()
        self.assertIsNone(self.db.get(ChildProfile, child_id).avatar)

    def test_child_limit_returns_409_and_rolls_back(self):
        create_child(ChildCreate(nickname="First"), parent_id=1, db=self.db)

        with patch.object(settings, "MAX_CHILDREN_PER_PARENT", 1):
            with self.assertRaises(ApiError) as caught:
                create_child(ChildCreate(nickname="Second"), parent_id=1, db=self.db)

        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.code, ErrorCode.LIMIT_REACHED)
        self.assertFalse(self.db.in_transaction())
        names = self.db.scalars(select(ChildProfile.nickname)).all()
        self.assertEqual(names, ["First"])

    def test_missing_locked_parent_returns_401(self):
        with self.assertRaises(ApiError) as caught:
            create_child(ChildCreate(nickname="Child"), parent_id=999, db=self.db)

        self.assertEqual(caught.exception.status_code, 401)
        self.assertFalse(self.db.in_transaction())

    def test_update_rolls_back_when_commit_fails(self):
        class FailingSession:
            def __init__(self):
                self.rolled_back = False

            def commit(self):
                raise RuntimeError("commit failed")

            def rollback(self):
                self.rolled_back = True

        child = ChildProfile(
            childID=10,
            parentID=1,
            nickname="Before",
            ageBand="junior",
        )
        failing_db = FailingSession()

        with self.assertRaisesRegex(RuntimeError, "commit failed"):
            update_child(
                ChildUpdate(nickname="After"),
                child=child,
                db=failing_db,
            )

        self.assertTrue(failing_db.rolled_back)


if __name__ == "__main__":
    unittest.main()
