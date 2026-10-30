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

from backend.app import database


class DatabaseDependencyTests(unittest.TestCase):
    def test_get_db_rolls_back_on_exception_and_always_closes(self):
        class FakeSession:
            def __init__(self):
                self.rollback_calls = 0
                self.close_calls = 0

            def rollback(self):
                self.rollback_calls += 1

            def close(self):
                self.close_calls += 1

        session = FakeSession()
        with patch.object(database, "SessionLocal", return_value=session):
            dependency = database.get_db()
            self.assertIs(next(dependency), session)
            with self.assertRaisesRegex(RuntimeError, "endpoint failed"):
                dependency.throw(RuntimeError("endpoint failed"))

        self.assertEqual(session.rollback_calls, 1)
        self.assertEqual(session.close_calls, 1)

    def test_get_db_closes_after_success(self):
        class FakeSession:
            def __init__(self):
                self.close_calls = 0

            def close(self):
                self.close_calls += 1

        session = FakeSession()
        with patch.object(database, "SessionLocal", return_value=session):
            dependency = database.get_db()
            self.assertIs(next(dependency), session)
            with self.assertRaises(StopIteration):
                next(dependency)

        self.assertEqual(session.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
