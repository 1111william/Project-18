import os
import unittest
from unittest.mock import MagicMock, patch

import sqlalchemy as sa


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_NAME", "coseat18_test")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from backend.app.config import settings
from backend.migrations import audit_existing as audit


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class LowerCaseModeConnection:
    def execute(self, statement, parameters=None):
        del parameters
        self.last_statement = str(statement)
        return ScalarResult(1)


class TableNameInspector:
    def get_table_names(self):
        return [name.lower() for name in audit.EXPECTED_COLUMNS]


class WrongCheckInspector:
    def get_check_constraints(self, table_name):
        if table_name == "QuizResult":
            return [
                {
                    "name": "ck_quiz_result_score_range",
                    "sqltext": "`score` >= -1 AND `score` <= 100",
                }
            ]
        return []


def reflected_type(kind, length):
    return {
        "bool": sa.Boolean(),
        "int": sa.Integer(),
        "str": sa.String(length),
        "text": sa.Text(),
        "datetime": sa.DateTime(),
    }[kind]


class BaselineTableInspector:
    def __init__(
        self,
        table_name,
        *,
        auto_increment=True,
        timestamp_default="CURRENT_TIMESTAMP",
        extra_uniques=(),
        foreign_keys=(),
    ):
        self.table_name = table_name
        self.auto_increment = auto_increment
        self.timestamp_default = timestamp_default
        self.extra_uniques = extra_uniques
        self.foreign_keys = list(foreign_keys)

    def get_columns(self, table_name):
        columns = []
        primary_key = audit.EXPECTED_PRIMARY_KEYS[table_name][0]
        for name, (kind, length, nullable) in audit.EXPECTED_COLUMNS[
            table_name
        ].items():
            column = {
                "name": name,
                "type": reflected_type(kind, length),
                "nullable": nullable,
                "default": None,
            }
            if name == primary_key:
                column["autoincrement"] = self.auto_increment
            if (table_name, name) in audit.REQUIRED_SERVER_DEFAULTS:
                column["default"] = self.timestamp_default
            columns.append(column)
        return columns

    def get_pk_constraint(self, table_name):
        return {"constrained_columns": audit.EXPECTED_PRIMARY_KEYS[table_name]}

    def get_foreign_keys(self, table_name):
        return self.foreign_keys

    def get_unique_constraints(self, table_name):
        uniques = audit.EXPECTED_UNIQUES.get(table_name, set()) | set(
            self.extra_uniques
        )
        return [{"column_names": columns} for columns in uniques]

    def get_indexes(self, table_name):
        return [
            {"column_names": columns, "unique": False}
            for columns in audit.EXPECTED_INDEXES.get(table_name, set())
        ]


class ExistingDatabaseAuditTests(unittest.TestCase):
    def test_windows_mysql_lowercase_tables_map_to_canonical_names(self):
        report = audit.AuditReport()
        resolved = audit._resolve_managed_table_names(
            LowerCaseModeConnection(),
            TableNameInspector(),
            report,
        )

        self.assertEqual(set(resolved), set(audit.EXPECTED_COLUMNS))
        self.assertEqual(resolved["ChildProfile"], "childprofile")
        self.assertFalse(report.errors)
        self.assertTrue(any("case-folded" in note for note in report.notes))

    def test_same_named_wrong_constraint_fails_audit(self):
        report = audit.AuditReport()
        table_names = {name: name for name in audit.EXPECTED_COLUMNS}
        audit._audit_check_constraints(
            WrongCheckInspector(),
            report,
            table_names,
            require_all=True,
        )
        self.assertTrue(any("score_range" in error for error in report.errors))

    def test_baseline_rejects_extra_check_constraints(self):
        report = audit.AuditReport()
        table_names = {name: name for name in audit.EXPECTED_COLUMNS}
        audit._audit_check_constraints(
            WrongCheckInspector(),
            report,
            table_names,
            require_all=False,
        )
        self.assertTrue(any("unexpected CHECK" in error for error in report.errors))

    def test_structure_rejects_non_auto_pk_fixed_time_and_extra_unique(self):
        report = audit.AuditReport()
        inspector = BaselineTableInspector(
            "Parent",
            auto_increment=False,
            timestamp_default="'2024-01-01 00:00:00'",
            extra_uniques={("displayName",)},
        )
        audit._audit_table_structure(inspector, report, {"Parent": "Parent"})

        self.assertTrue(any("AUTO_INCREMENT" in error for error in report.errors))
        self.assertTrue(
            any("CURRENT_TIMESTAMP" in error for error in report.errors)
        )
        self.assertTrue(any("unexpected unique" in error for error in report.errors))

    def test_structure_rejects_composite_foreign_key(self):
        report = audit.AuditReport()
        inspector = BaselineTableInspector(
            "Parent",
            foreign_keys=[
                {
                    "name": "fk_extra_composite",
                    "constrained_columns": ["parentID", "email"],
                    "referred_table": "Other",
                    "referred_columns": ["id", "email"],
                    "options": {},
                }
            ],
        )
        audit._audit_table_structure(inspector, report, {"Parent": "Parent"})
        self.assertTrue(any("composite/malformed" in error for error in report.errors))

    def test_current_timestamp_default_spellings_are_semantic(self):
        for value in (
            "CURRENT_TIMESTAMP",
            "current_timestamp()",
            "now()",
            "(now())",
            "((CURRENT_TIMESTAMP()))",
        ):
            with self.subTest(value=value):
                self.assertTrue(audit._is_current_timestamp_default(value))
        self.assertFalse(audit._is_current_timestamp_default("'2024-01-01'"))

    def test_cli_engine_uses_core_tls_connect_args(self):
        fake_engine = MagicMock()
        fake_connection = fake_engine.connect.return_value.__enter__.return_value
        passing_report = audit.AuditReport()

        with (
            patch.object(audit.sa, "create_engine", return_value=fake_engine) as create,
            patch.object(
                audit,
                "audit_connection",
                return_value=passing_report,
            ) as audit_call,
            patch.object(audit, "_print_report"),
        ):
            result = audit.main([])

        self.assertEqual(result, 0)
        create.assert_called_once_with(
            settings.database_url,
            connect_args=settings.database_connect_args,
            poolclass=audit.NullPool,
        )
        audit_call.assert_called_once_with(
            fake_connection,
            require_unversioned=False,
        )
        fake_engine.dispose.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
