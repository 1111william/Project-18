import importlib
import io
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util import CommandError


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_NAME", "coseat18_test")
os.environ.setdefault("DB_SSL_MODE", "disabled")


BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
HARDENING = importlib.import_module(
    "backend.migrations.versions.20261004_0002_harden_constraints"
)
from backend.migrations.autogenerate_safety import (
    reject_case_folded_autogenerate,
)


def offline_sql(revision: str) -> str:
    output = io.StringIO()
    config = Config(str(ALEMBIC_INI), output_buffer=output)
    command.upgrade(config, revision, sql=True)
    return output.getvalue()


class DatabaseMigrationTests(unittest.TestCase):
    def test_case_folded_mysql_refuses_dangerous_autogenerate(self):
        class ScalarResult:
            def scalar_one(self):
                return 1

        class Connection:
            dialect = SimpleNamespace(name="mysql")

            def exec_driver_sql(self, statement):
                self.statement = statement
                return ScalarResult()

        with self.assertRaisesRegex(CommandError, "destructive drop/create"):
            reject_case_folded_autogenerate(
                Connection(),
                autogenerate_requested=True,
            )

    def test_revision_chain_has_frozen_baseline_then_hardening(self):
        scripts = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
        self.assertEqual(scripts.get_base(), "20261004_0001")
        self.assertEqual(scripts.get_current_head(), "20261004_0002")
        revisions = [revision.revision for revision in scripts.walk_revisions()]
        self.assertEqual(revisions, ["20261004_0002", "20261004_0001"])

    def test_baseline_offline_sql_freezes_original_schema(self):
        sql = offline_sql("20261004_0001")
        for table_name in HARDENING.TABLES:
            self.assertIn(f"CREATE TABLE `{table_name}`", sql)
        self.assertNotIn("ck_progress_percent_complete_range", sql)
        self.assertNotIn("CONVERT TO CHARACTER SET", sql)

    def test_head_offline_sql_contains_charset_and_all_named_checks(self):
        sql = offline_sql("head")
        for table_name in HARDENING.TABLES:
            self.assertIn(
                f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET utf8mb4",
                sql,
            )
        for checks in HARDENING.CHECKS.values():
            for constraint_name, _condition in checks:
                self.assertIn(constraint_name, sql)

    def test_same_named_wrong_check_is_rejected_before_skip(self):
        wrong = {"ck_quiz_result_score_range": "`score` >= -1"}
        with patch.object(HARDENING, "_reflected_checks", return_value=wrong):
            with self.assertRaisesRegex(RuntimeError, "different definitions"):
                HARDENING._assert_existing_checks_match(object())

    def test_check_sql_normalisation_allows_reflection_parentheses_only(self):
        reflected = "((`score` >= 0) and (`score` <= 100))"
        expected = "`score` >= 0 AND `score` <= 100"
        self.assertEqual(
            HARDENING._normalise_check_sql(reflected),
            HARDENING._normalise_check_sql(expected),
        )


if __name__ == "__main__":
    unittest.main()
