import asyncio
import base64
import json
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from backend.app.core.responses import ApiError, ErrorCode
from backend.app.models import ChildProfile, Parent
from backend.app.routers.children import (
    AVATAR_DIRECTORY,
    create_child,
    delete_child,
    list_children,
    remove_custom_avatar,
    update_child,
    upload_avatar,
)
from backend.app.schemas.child import ChildCreate, ChildDeleteConfirm, ChildUpdate
from backend.app.services.account_auth import registration_challenges


class ChildProfileApiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Parent.__table__.create(self.engine)
        ChildProfile.__table__.create(self.engine)
        self.db = Session(self.engine)
        parent = Parent(
            email="parent@example.test",
            passwordHash="test-only",
            displayName="Test Parent",
        )
        self.db.add(parent)
        self.db.commit()
        self.db.refresh(parent)
        self.parent_id = parent.parentID

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_create_list_update_and_delete_child(self):
        create_child(
            ChildCreate(nickname="Mira", age=11, avatar="bunny"),
            parent_id=self.parent_id,
            db=self.db,
        )
        child = self.db.scalar(select(ChildProfile))
        self.assertIsNotNone(child)
        self.assertEqual(child.nickname, "Mira")
        self.assertEqual(child.age, 11)
        self.assertEqual(child.avatar, "bunny")

        payload = json.loads(list_children(parent_id=self.parent_id, db=self.db).body)
        self.assertEqual(payload["data"][0]["nickname"], "Mira")
        self.assertEqual(payload["data"][0]["age"], 11)

        update_child(
            ChildUpdate(nickname="Mina", age=12, avatar="flower"),
            child=child,
            db=self.db,
        )
        self.db.refresh(child)
        self.assertEqual((child.nickname, child.age, child.avatar), ("Mina", 12, "flower"))

        challenge, code = registration_challenges.create_child_delete(
            "parent@example.test",
            self.parent_id,
            child.childID,
        )
        wrong_code = "000000" if code != "000000" else "999999"
        with self.assertRaises(ApiError) as raised:
            delete_child(
                ChildDeleteConfirm(challenge_id=challenge.challenge_id, code=wrong_code),
                child=child,
                db=self.db,
            )
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIsNotNone(self.db.scalar(select(ChildProfile)))

        delete_child(
            ChildDeleteConfirm(challenge_id=challenge.challenge_id, code=code),
            child=child,
            db=self.db,
        )
        self.assertIsNone(self.db.scalar(select(ChildProfile)))

    def test_sixth_child_is_rejected(self):
        for index in range(5):
            create_child(
                ChildCreate(nickname=f"Child {index + 1}", age=10 + index, avatar="sprout"),
                parent_id=self.parent_id,
                db=self.db,
            )

        with self.assertRaises(ApiError) as raised:
            create_child(
                ChildCreate(nickname="Child 6", age=9, avatar="koala"),
                parent_id=self.parent_id,
                db=self.db,
            )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.code, ErrorCode.LIMIT_REACHED)

    def test_custom_avatar_upload_is_saved(self):
        image = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            sent = True
            return {"type": "http.request", "body": image, "more_body": False}

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/children/avatar",
                "headers": [
                    (b"content-type", b"image/png"),
                    (b"content-length", str(len(image)).encode("ascii")),
                ],
            },
            receive,
        )
        response = asyncio.run(upload_avatar(request, parent_id=self.parent_id))
        payload = json.loads(response.body)
        avatar = payload["data"]["avatar"]
        filename = avatar.removeprefix("custom:")
        try:
            self.assertTrue((AVATAR_DIRECTORY / filename).is_file())
        finally:
            remove_custom_avatar(avatar)


if __name__ == "__main__":
    unittest.main()
