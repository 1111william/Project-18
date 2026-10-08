"""Opt-in real MySQL + real HTTP regression tests (never a login-flow test).

Run only on a migrated, disposable local database whose name ends in _test.
Set RUN_MYSQL_TESTS=1, APP_ENV=test and DB_* before unittest discovery.
Fixtures are isolated and removed; no schema is dropped or created here.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import sysconfig
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from itsdangerous import TimestampSigner
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.app.config import settings
from backend.app.database import SessionLocal, engine
from backend.app.models import ChildProfile, LearningLevel, Lesson, Parent, Progress, Quiz, QuizResult


ROOT = Path(__file__).resolve().parents[2]
ENABLED = os.environ.get("RUN_MYSQL_TESTS") == "1"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class RunningAPI:
    def __init__(self, overrides=None):
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.log = tempfile.TemporaryFile(mode="w+b")
        env = dict(os.environ, PYTHON_DOTENV_DISABLED="1", PYTHONUTF8="1")
        env.update(overrides or {})
        # On Windows run the underlying interpreter directly so terminate()
        # cannot leave a venv-launcher child listening after the test finishes.
        executable = sys.executable
        if os.name == "nt":
            executable = getattr(sys, "_base_executable", sys.executable)
            env["PYTHONPATH"] = os.pathsep.join([str(ROOT), sysconfig.get_path("purelib")])
        self.process = subprocess.Popen(
            [executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1",
             "--port", str(self.port), "--no-proxy-headers", "--no-access-log"],
            cwd=ROOT, env=env, stdout=self.log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    break
                try:
                    if self.request("GET", "/api/live")[0] == 200:
                        return
                except (URLError, TimeoutError, ConnectionError):
                    time.sleep(0.1)
            self.log.seek(0)
            raise RuntimeError("Test API failed to start: " + self.log.read().decode(errors="replace"))
        except BaseException:
            self.close()
            raise

    def request(self, method, path, *, cookie=None, body=None, origin=None, extra=None):
        headers = {"Accept": "application/json"}
        if cookie is not None:
            headers["Cookie"] = f"{settings.SESSION_COOKIE_NAME}={cookie}"
        if origin is not None:
            headers["Origin"] = origin
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        headers.update(extra or {})
        request = Request(self.url + path, method=method, data=data, headers=headers)
        try:
            response = build_opener(ProxyHandler({})).open(request, timeout=15)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            try:
                result = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                result = raw.decode("utf-8")
            return response.status, result, response.headers

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.log.close()


@unittest.skipUnless(ENABLED, "Set RUN_MYSQL_TESTS=1 for disposable local MySQL tests")
class MySQLHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (settings.APP_ENV != "test" or settings.DB_HOST not in {"127.0.0.1", "localhost", "::1"}
                or not settings.DB_NAME.endswith("_test")):
            raise RuntimeError("Refusing integration tests: require APP_ENV=test, loopback DB, name ending _test")
        with engine.connect() as connection:
            if connection.scalar(text("SELECT DATABASE()")) != settings.DB_NAME:
                raise RuntimeError("Refusing integration tests: selected database differs from settings")
            if connection.scalar(text("SELECT version_num FROM alembic_version")) != "20261004_0002":
                raise RuntimeError("Refusing integration tests: disposable database must be migrated to head")
        cls.api = RunningAPI()
        cls.addClassCleanup(cls.api.close)
        cls.addClassCleanup(engine.dispose)

    def setUp(self):
        self.token = secrets.token_hex(8)
        self.parent_ids = []
        self.level_id = None
        self.addCleanup(self.clean_fixtures)
        with SessionLocal.begin() as db:
            parents = [Parent(email=f"{self.token}-{i}@example.test", passwordHash="test-not-a-login-hash",
                              displayName="Integration test", isAdmin=False) for i in range(2)]
            db.add_all(parents)
            db.flush()
            self.parent_ids = [p.parentID for p in parents]
            order = db.scalar(select(func.max(LearningLevel.levelOrder))) or 0
            level = LearningLevel(levelOrder=order + 1, title="Test বাংলা", passMark=70)
            db.add(level)
            db.flush()
            self.level_id = level.levelID
            lesson = Lesson(levelID=level.levelID, strand="reading", lessonOrder=1, title="Test lesson")
            db.add(lesson)
            db.flush()
            self.lesson_id = lesson.lessonID
            quiz = Quiz(lessonID=lesson.lessonID, title="Test quiz")
            child = ChildProfile(parentID=self.parent_ids[0], nickname="শিশু 😀", ageBand="junior")
            db.add_all([quiz, child])
            db.flush()
            self.quiz_id, self.child_id = quiz.quizID, child.childID
        self.cookie = self.sign({"parentID": self.parent_ids[0]})
        self.other_cookie = self.sign({"parentID": self.parent_ids[1], "isAdmin": True})

    def clean_fixtures(self):
        with SessionLocal.begin() as db:
            if self.parent_ids:
                db.execute(delete(Parent).where(Parent.parentID.in_(self.parent_ids)))
            if self.level_id:
                db.execute(delete(LearningLevel).where(LearningLevel.levelID == self.level_id))

    @staticmethod
    def sign(payload):
        data = base64.b64encode(json.dumps(payload).encode())
        return TimestampSigner(settings.SESSION_SECRET).sign(data).decode()

    def expect(self, response, status, code=None):
        actual, body, headers = response
        self.assertEqual(actual, status, body)
        self.assertEqual(body["success"], status < 400, body)
        if code:
            self.assertEqual(body["code"], code)
        return body, headers

    def test_live_health_and_framework_errors(self):
        for path in ("/", "/api/live", "/api/health"):
            with self.subTest(path=path):
                self.expect(self.api.request("GET", path), 200)
        self.expect(self.api.request("GET", "/no-such-route"), 404, "NOT_FOUND")
        _, headers = self.expect(self.api.request("POST", "/api/health"), 405, "METHOD_NOT_ALLOWED")
        self.assertIn("GET", headers["Allow"])

    def test_authentication_and_ownership(self):
        self.expect(self.api.request("GET", "/api/children"), 401, "UNAUTHENTICATED")
        self.expect(self.api.request("GET", "/api/children", cookie="tampered"), 401, "UNAUTHENTICATED")
        for parent_id in (True, 1.5, "bad", 0):
            with self.subTest(parent_id=parent_id):
                self.expect(self.api.request("GET", "/api/children", cookie=self.sign({"parentID": parent_id})),
                            401, "UNAUTHENTICATED")
        self.expect(self.api.request("GET", f"/api/children/{self.child_id}", cookie=self.other_cookie),
                    403, "FORBIDDEN")
        with SessionLocal.begin() as db:
            db.execute(delete(Parent).where(Parent.parentID == self.parent_ids[0]))
        self.expect(self.api.request("GET", "/api/children", cookie=self.cookie), 401, "UNAUTHENTICATED")

    def test_unicode_crud_and_null_clearing(self):
        body, _ = self.expect(self.api.request("POST", "/api/children", cookie=self.cookie,
            origin=self.api.url, body={"nickname": "  বাংলা 😀  ", "avatar": "test.png", "ageBand": "junior"}), 200)
        child_id = body["data"]["childID"]
        body, _ = self.expect(self.api.request("GET", f"/api/children/{child_id}", cookie=self.cookie), 200)
        self.assertEqual(body["data"]["nickname"], "বাংলা 😀")
        self.expect(self.api.request("PUT", f"/api/children/{child_id}", cookie=self.cookie,
            origin=self.api.url, body={"avatar": None}), 200)
        body, _ = self.expect(self.api.request("GET", f"/api/children/{child_id}", cookie=self.cookie), 200)
        self.assertIsNone(body["data"]["avatar"])
        self.assertEqual(body["data"]["nickname"], "বাংলা 😀")
        self.expect(self.api.request("DELETE", f"/api/children/{child_id}", cookie=self.cookie, origin=self.api.url), 200)
        self.expect(self.api.request("GET", f"/api/children/{child_id}", cookie=self.cookie), 404, "NOT_FOUND")

    def test_validation_does_not_change_existing_data(self):
        for payload in ({"nickname": "   "}, {"nickname": None}, {"ageBand": None}, {"ageBand": "wrong"}):
            with self.subTest(payload=payload):
                self.expect(self.api.request("PUT", f"/api/children/{self.child_id}", cookie=self.cookie,
                    origin=self.api.url, body=payload), 400, "VALIDATION_FAILED")
        self.expect(self.api.request("GET", "/api/children/invalid", cookie=self.cookie), 400, "VALIDATION_FAILED")
        self.expect(self.api.request("GET", f"/api/children/{self.child_id}", cookie=self.cookie), 200)

    def test_csrf_and_cors(self):
        for origin in (None, "https://untrusted.example", "null"):
            with self.subTest(origin=origin):
                self.expect(self.api.request("PUT", f"/api/children/{self.child_id}", cookie=self.cookie,
                    origin=origin, body={"nickname": "blocked"}), 403, "CSRF_FAILED")
        origin = settings.allowed_origins[0]
        _, headers = self.expect(self.api.request("PUT", f"/api/children/{self.child_id}", cookie=self.cookie,
            origin=origin, body={"nickname": "allowed"}), 200)
        self.assertEqual(headers["Access-Control-Allow-Origin"], origin)
        self.assertEqual(headers["Access-Control-Allow-Credentials"], "true")
        _, headers = self.expect(self.api.request("GET", "/missing", origin=origin), 404, "NOT_FOUND")
        self.assertEqual(headers["Access-Control-Allow-Origin"], origin)

    def test_browser_preflight_allows_credentialed_json_write(self):
        origin = settings.allowed_origins[0]
        status, _, headers = self.api.request("OPTIONS", f"/api/children/{self.child_id}", origin=origin,
            extra={"Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Access-Control-Allow-Origin"], origin)
        self.assertEqual(headers["Access-Control-Allow-Credentials"], "true")
        self.assertIn("PUT", headers["Access-Control-Allow-Methods"])

    def test_invalid_session_cookie_is_cleared_with_http_only_flags(self):
        _, headers = self.expect(self.api.request("GET", "/api/children",
            cookie=self.sign({"parentID": "invalid"})), 401, "UNAUTHENTICATED")
        cookie = headers["Set-Cookie"].lower()
        self.assertIn("expires=thu, 01 jan 1970", cookie)
        self.assertIn("httponly", cookie)
        self.assertIn(f"samesite={settings.SESSION_COOKIE_SAMESITE}", cookie)

    def test_concurrent_creation_cannot_exceed_child_limit(self):
        with SessionLocal.begin() as db:
            for i in range(settings.MAX_CHILDREN_PER_PARENT - 2):
                db.add(ChildProfile(parentID=self.parent_ids[0], nickname=f"existing{i}", ageBand="junior"))
        def create_one(index):
            return self.api.request("POST", "/api/children", cookie=self.cookie, origin=self.api.url,
                                    body={"nickname": f"concurrent{index}", "ageBand": "junior"})
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(create_one, range(8)))
        self.assertEqual(sorted(r[0] for r in responses), [200] + [409] * 7, responses)
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ChildProfile).where(
                ChildProfile.parentID == self.parent_ids[0])), settings.MAX_CHILDREN_PER_PARENT)

    def test_database_constraints_and_foreign_keys(self):
        invalid = [Progress(childID=self.child_id, lessonID=self.lesson_id, percentComplete=101),
                   Progress(childID=self.child_id, lessonID=self.lesson_id, secondsSpent=-1),
                   ChildProfile(parentID=2147483647, nickname="orphan"),
                   QuizResult(childID=self.child_id, quizID=self.quiz_id, score=101, correctCount=1, totalCount=1),
                   QuizResult(childID=self.child_id, quizID=self.quiz_id, score=100, correctCount=2, totalCount=1)]
        for row in invalid:
            with self.subTest(model=type(row).__name__), SessionLocal() as db:
                db.add(row)
                with self.assertRaises((IntegrityError, OperationalError)):
                    db.flush()
                db.rollback()
        with SessionLocal.begin() as db:
            db.add(Progress(childID=self.child_id, lessonID=self.lesson_id, percentComplete=100))
        with SessionLocal() as db:
            db.add(Progress(childID=self.child_id, lessonID=self.lesson_id))
            with self.assertRaises(IntegrityError):
                db.flush()
            db.rollback()

    def test_parent_deletion_cascades_learning_records(self):
        with SessionLocal.begin() as db:
            db.add(Progress(childID=self.child_id, lessonID=self.lesson_id))
            db.add(QuizResult(childID=self.child_id, quizID=self.quiz_id, score=100, correctCount=1, totalCount=1))
        with SessionLocal.begin() as db:
            db.execute(delete(Parent).where(Parent.parentID == self.parent_ids[0]))
        with SessionLocal() as db:
            self.assertIsNone(db.get(ChildProfile, self.child_id))
            self.assertEqual(db.scalar(select(func.count()).select_from(Progress).where(Progress.childID == self.child_id)), 0)
            self.assertEqual(db.scalar(select(func.count()).select_from(QuizResult).where(QuizResult.childID == self.child_id)), 0)

    def test_orm_level_delete_respects_database_cascade_with_loaded_lessons(self):
        with SessionLocal.begin() as db:
            level = db.get(LearningLevel, self.level_id)
            self.assertEqual(len(level.lessons), 1)
            db.delete(level)
        with SessionLocal() as db:
            self.assertIsNone(db.get(Lesson, self.lesson_id))
            self.assertIsNone(db.get(Quiz, self.quiz_id))

    def test_database_outage_has_safe_503_but_live_stays_up(self):
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
            api = RunningAPI({"DATABASE_URL": f"mysql+pymysql://unused:fake@127.0.0.1:{port}/outage_test",
                              "DB_CONNECT_TIMEOUT": "1"})
            try:
                self.expect(api.request("GET", "/api/live"), 200)
                body, _ = self.expect(api.request("GET", "/api/health"), 503, "DB_UNAVAILABLE")
                self.assertNotIn("fake", json.dumps(body))
                self.expect(api.request("GET", "/api/children", cookie=self.cookie), 503, "DB_UNAVAILABLE")
            finally:
                api.close()


if __name__ == "__main__":
    unittest.main()
