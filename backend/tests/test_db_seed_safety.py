import os
import unittest
from unittest.mock import patch

import sqlalchemy as sa
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_NAME", "coseat18_test")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from backend.app.database import Base
from backend.app.models import QuizQuestion, QuizResult
from backend.scripts import seed


def target(*, host="127.0.0.1", database="coseat18_test"):
    return URL.create(
        "mysql+pymysql",
        username="root",
        password="",
        host=host,
        port=3306,
        database=database,
        query={"charset": "utf8mb4"},
    )


class SeedSafetyTests(unittest.TestCase):
    def test_safe_local_test_target_is_allowed_without_reset(self):
        errors = seed.seed_safety_errors(
            app_env="test",
            database_url=target(),
        )
        self.assertEqual(errors, [])

    def test_final_parsed_url_host_controls_remote_rejection(self):
        errors = seed.seed_safety_errors(
            app_env="development",
            database_url=target(host="shared-db.example.com"),
        )
        self.assertTrue(any("parsed database URL host" in error for error in errors))

    def test_compose_service_name_is_not_a_localhost_bypass(self):
        errors = seed.seed_safety_errors(
            app_env="development",
            database_url=target(host="db", database="coseat18_dev"),
        )
        self.assertTrue(any("parsed database URL host" in error for error in errors))

    def test_database_name_requires_separate_dev_or_test_marker(self):
        for database in ("coseat18", "contest", "devotion", "production"):
            with self.subTest(database=database):
                errors = seed.seed_safety_errors(
                    app_env="test",
                    database_url=target(database=database),
                )
                self.assertTrue(any("database name" in error for error in errors))

    def test_reset_requires_exact_name_and_second_confirmation(self):
        errors = seed.seed_safety_errors(
            app_env="development",
            database_url=target(database="coseat18_dev"),
            reset=True,
            confirm_database="wrong_dev",
            yes_really_reset=False,
        )
        self.assertTrue(any("exactly match" in error for error in errors))
        self.assertTrue(any("yes-really-reset" in error for error in errors))

        allowed = seed.seed_safety_errors(
            app_env="development",
            database_url=target(database="coseat18_dev"),
            reset=True,
            confirm_database="coseat18_dev",
            yes_really_reset=True,
        )
        self.assertEqual(allowed, [])

    def test_default_cli_never_calls_reset(self):
        with (
            patch.object(seed, "validate_seed_target") as validate,
            patch.object(
                seed,
                "_prepare_demo_password_hash",
                return_value="prepared-hash",
            ),
            patch.object(seed, "_reset_schema_to_head") as reset_schema,
            patch.object(seed, "_seed_empty_database") as seed_database,
        ):
            result = seed.main([])

        self.assertEqual(result, 0)
        validate.assert_called_once_with(
            reset=False,
            confirm_database=None,
            yes_really_reset=False,
        )
        reset_schema.assert_not_called()
        seed_database.assert_called_once_with(password_hash="prepared-hash")

    def test_invalid_demo_password_is_rejected_before_reset(self):
        invalid_passwords = ("too-short", "界" * 25)
        for invalid_password in invalid_passwords:
            with self.subTest(password=invalid_password):
                with (
                    patch.dict(
                        os.environ,
                        {"DEMO_PARENT_PASSWORD": invalid_password},
                    ),
                    patch.object(seed, "validate_seed_target"),
                    patch.object(seed, "_reset_schema_to_head") as reset_schema,
                    patch.object(seed, "_seed_empty_database") as seed_database,
                ):
                    result = seed.main(
                        [
                            "--reset",
                            "--confirm-database",
                            "coseat18_test",
                            "--yes-really-reset",
                        ]
                    )

                self.assertEqual(result, 2)
                reset_schema.assert_not_called()
                seed_database.assert_not_called()

    def test_reset_refuses_unmanaged_foreign_key_to_managed_table(self):
        class ExternalInspector:
            def get_table_names(self):
                return ["Parent", "plugin_audit"]

            def get_foreign_keys(self, table_name):
                if table_name == "plugin_audit":
                    return [
                        {
                            "name": "fk_plugin_parent",
                            "referred_table": "Parent",
                        }
                    ]
                return []

        with patch.object(seed.sa, "inspect", return_value=ExternalInspector()):
            with self.assertRaisesRegex(
                seed.SeedSafetyError,
                "unmanaged table foreign keys",
            ):
                seed._require_no_external_foreign_keys(object())

    def test_seed_session_rolls_back_and_closes_on_write_failure(self):
        class FakeSession:
            def __init__(self):
                self.connection_value = object()
                self.rollback_calls = 0
                self.close_calls = 0

            def connection(self):
                return self.connection_value

            def rollback(self):
                self.rollback_calls += 1

            def close(self):
                self.close_calls += 1

        fake = FakeSession()
        with (
            patch.object(seed, "SessionLocal", return_value=fake),
            patch.object(seed, "_require_head_revision"),
            patch.object(seed, "_require_managed_tables_empty"),
            patch.object(
                seed,
                "seed_demo_data",
                side_effect=RuntimeError("write failed"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "write failed"):
                seed._seed_empty_database(password_hash="prepared-hash")

        self.assertEqual(fake.rollback_calls, 1)
        self.assertEqual(fake.close_calls, 1)

    def test_demo_dataset_is_constraint_valid_and_quiz_two_is_consistent(self):
        sqlite_engine = sa.create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(sqlite_engine)
        try:
            with Session(sqlite_engine) as session:
                password_hash = seed._prepare_demo_password_hash(
                    "local-demo-password"
                )
                seed.seed_demo_data(
                    session,
                    password_hash=password_hash,
                )
                session.commit()

                result = session.scalar(
                    sa.select(QuizResult).where(QuizResult.quizID == 2)
                )
                question_count = session.scalar(
                    sa.select(sa.func.count())
                    .select_from(QuizQuestion)
                    .where(QuizQuestion.quizID == 2)
                )

                self.assertIsNotNone(result)
                self.assertEqual(result.totalCount, question_count)
                self.assertEqual(result.correctCount, 1)
                self.assertEqual(result.score, 100)
                self.assertTrue(result.passed)
        finally:
            sqlite_engine.dispose()


if __name__ == "__main__":
    unittest.main()
