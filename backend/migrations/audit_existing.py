"""Read-only preflight for adopting Alembic on an existing database.

This command never creates, alters, drops, stamps, or cleans anything. It
validates the managed eleven-table baseline and the data predicates required by
the hardening migration so a human can decide whether stamping is safe.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.config import settings  # noqa: E402


EXPECTED_COLUMNS: dict[str, dict[str, tuple[str, int | None, bool]]] = {
    "Parent": {
        "parentID": ("int", None, False),
        "email": ("str", 150, False),
        "passwordHash": ("str", 255, False),
        "displayName": ("str", 100, False),
        "pinHash": ("str", 255, True),
        "otpCode": ("str", 10, True),
        "otpExpiresAt": ("datetime", None, True),
        "isAdmin": ("bool", None, False),
        "createdAt": ("datetime", None, False),
    },
    "LearningLevel": {
        "levelID": ("int", None, False),
        "levelOrder": ("int", None, False),
        "title": ("str", 100, False),
        "description": ("str", 255, True),
        "passMark": ("int", None, False),
    },
    "ChildProfile": {
        "childID": ("int", None, False),
        "parentID": ("int", None, False),
        "nickname": ("str", 60, False),
        "avatar": ("str", 150, True),
        "ageBand": ("str", 20, False),
        "currentLevelID": ("int", None, True),
        "createdAt": ("datetime", None, False),
    },
    "Lesson": {
        "lessonID": ("int", None, False),
        "levelID": ("int", None, False),
        "strand": ("str", 20, False),
        "lessonOrder": ("int", None, False),
        "title": ("str", 150, False),
        "summary": ("str", 255, True),
        "coverImage": ("str", 150, True),
        "estimatedMinutes": ("int", None, False),
        "isPublished": ("bool", None, False),
    },
    "LearningContent": {
        "contentID": ("int", None, False),
        "lessonID": ("int", None, False),
        "blockOrder": ("int", None, False),
        "blockKind": ("str", 20, False),
        "textContent": ("text", None, True),
        "banglaText": ("text", None, True),
        "mediaPath": ("str", 150, True),
        "caption": ("str", 255, True),
    },
    "AudioResource": {
        "audioID": ("int", None, False),
        "lessonID": ("int", None, True),
        "contentID": ("int", None, True),
        "label": ("str", 100, False),
        "filePath": ("str", 200, False),
        "source": ("str", 10, False),
        "verified": ("bool", None, False),
        "createdAt": ("datetime", None, False),
    },
    "Quiz": {
        "quizID": ("int", None, False),
        "lessonID": ("int", None, False),
        "title": ("str", 150, False),
        "passMark": ("int", None, False),
    },
    "QuizQuestion": {
        "questionID": ("int", None, False),
        "quizID": ("int", None, False),
        "questionOrder": ("int", None, False),
        "questionKind": ("str", 20, False),
        "prompt": ("str", 255, False),
        "mediaPath": ("str", 150, True),
    },
    "QuizOption": {
        "optionID": ("int", None, False),
        "questionID": ("int", None, False),
        "optionOrder": ("int", None, False),
        "optionText": ("str", 255, False),
        "isCorrect": ("bool", None, False),
    },
    "Progress": {
        "progressID": ("int", None, False),
        "childID": ("int", None, False),
        "lessonID": ("int", None, False),
        "percentComplete": ("int", None, False),
        "completed": ("bool", None, False),
        "secondsSpent": ("int", None, False),
        "lastViewedAt": ("datetime", None, False),
    },
    "QuizResult": {
        "resultID": ("int", None, False),
        "childID": ("int", None, False),
        "quizID": ("int", None, False),
        "score": ("int", None, False),
        "correctCount": ("int", None, False),
        "totalCount": ("int", None, False),
        "passed": ("bool", None, False),
        "attemptNumber": ("int", None, False),
        "submittedAt": ("datetime", None, False),
    },
}

EXPECTED_PRIMARY_KEYS = {
    "Parent": ("parentID",),
    "LearningLevel": ("levelID",),
    "ChildProfile": ("childID",),
    "Lesson": ("lessonID",),
    "LearningContent": ("contentID",),
    "AudioResource": ("audioID",),
    "Quiz": ("quizID",),
    "QuizQuestion": ("questionID",),
    "QuizOption": ("optionID",),
    "Progress": ("progressID",),
    "QuizResult": ("resultID",),
}

EXPECTED_FOREIGN_KEYS: dict[str, set[tuple[str, str, str, str]]] = {
    "Parent": set(),
    "LearningLevel": set(),
    "ChildProfile": {
        ("parentID", "Parent", "parentID", "CASCADE"),
        ("currentLevelID", "LearningLevel", "levelID", "SET NULL"),
    },
    "Lesson": {("levelID", "LearningLevel", "levelID", "CASCADE")},
    "LearningContent": {("lessonID", "Lesson", "lessonID", "CASCADE")},
    "AudioResource": {
        ("lessonID", "Lesson", "lessonID", "CASCADE"),
        ("contentID", "LearningContent", "contentID", "CASCADE"),
    },
    "Quiz": {("lessonID", "Lesson", "lessonID", "CASCADE")},
    "QuizQuestion": {("quizID", "Quiz", "quizID", "CASCADE")},
    "QuizOption": {("questionID", "QuizQuestion", "questionID", "CASCADE")},
    "Progress": {
        ("childID", "ChildProfile", "childID", "CASCADE"),
        ("lessonID", "Lesson", "lessonID", "CASCADE"),
    },
    "QuizResult": {
        ("childID", "ChildProfile", "childID", "CASCADE"),
        ("quizID", "Quiz", "quizID", "CASCADE"),
    },
}

EXPECTED_UNIQUES: dict[str, set[tuple[str, ...]]] = {
    "Parent": {("email",)},
    "LearningLevel": {("levelOrder",)},
    "Progress": {("childID", "lessonID")},
}

EXPECTED_INDEXES: dict[str, set[tuple[str, ...]]] = {
    "ChildProfile": {("parentID",), ("currentLevelID",)},
    "Lesson": {("levelID",), ("strand",)},
    "LearningContent": {("lessonID",)},
    "AudioResource": {("lessonID",), ("contentID",)},
    "Quiz": {("lessonID",)},
    "QuizQuestion": {("quizID",)},
    "QuizOption": {("questionID",)},
    "Progress": {("lessonID",)},
    "QuizResult": {("childID",), ("quizID",)},
}

REQUIRED_SERVER_DEFAULTS = {
    ("Parent", "createdAt"),
    ("ChildProfile", "createdAt"),
    ("AudioResource", "createdAt"),
    ("Progress", "lastViewedAt"),
    ("QuizResult", "submittedAt"),
}

INVALID_DATA_PREDICATES: tuple[tuple[str, str, str], ...] = (
    ("ck_learning_level_order_positive", "LearningLevel", "`levelOrder` <= 0"),
    (
        "ck_learning_level_pass_mark_range",
        "LearningLevel",
        "`passMark` < 0 OR `passMark` > 100",
    ),
    ("ck_lesson_order_positive", "Lesson", "`lessonOrder` <= 0"),
    (
        "ck_lesson_estimated_minutes_nonnegative",
        "Lesson",
        "`estimatedMinutes` < 0",
    ),
    (
        "ck_learning_content_block_order_positive",
        "LearningContent",
        "`blockOrder` <= 0",
    ),
    (
        "ck_quiz_pass_mark_range",
        "Quiz",
        "`passMark` < 0 OR `passMark` > 100",
    ),
    (
        "ck_quiz_question_order_positive",
        "QuizQuestion",
        "`questionOrder` <= 0",
    ),
    (
        "ck_quiz_option_order_positive",
        "QuizOption",
        "`optionOrder` <= 0",
    ),
    (
        "ck_progress_percent_complete_range",
        "Progress",
        "`percentComplete` < 0 OR `percentComplete` > 100",
    ),
    (
        "ck_progress_seconds_spent_nonnegative",
        "Progress",
        "`secondsSpent` < 0",
    ),
    (
        "ck_quiz_result_score_range",
        "QuizResult",
        "`score` < 0 OR `score` > 100",
    ),
    (
        "ck_quiz_result_correct_count_nonnegative",
        "QuizResult",
        "`correctCount` < 0",
    ),
    (
        "ck_quiz_result_total_count_positive",
        "QuizResult",
        "`totalCount` <= 0",
    ),
    (
        "ck_quiz_result_correct_lte_total",
        "QuizResult",
        "`correctCount` > `totalCount`",
    ),
    (
        "ck_quiz_result_attempt_number_positive",
        "QuizResult",
        "`attemptNumber` <= 0",
    ),
)

EXPECTED_CHECK_SQL: dict[str, dict[str, str]] = {
    "LearningLevel": {
        "ck_learning_level_order_positive": "`levelOrder` > 0",
        "ck_learning_level_pass_mark_range": (
            "`passMark` >= 0 AND `passMark` <= 100"
        ),
    },
    "Lesson": {
        "ck_lesson_order_positive": "`lessonOrder` > 0",
        "ck_lesson_estimated_minutes_nonnegative": "`estimatedMinutes` >= 0",
    },
    "LearningContent": {
        "ck_learning_content_block_order_positive": "`blockOrder` > 0",
    },
    "Quiz": {
        "ck_quiz_pass_mark_range": "`passMark` >= 0 AND `passMark` <= 100",
    },
    "QuizQuestion": {
        "ck_quiz_question_order_positive": "`questionOrder` > 0",
    },
    "QuizOption": {
        "ck_quiz_option_order_positive": "`optionOrder` > 0",
    },
    "Progress": {
        "ck_progress_percent_complete_range": (
            "`percentComplete` >= 0 AND `percentComplete` <= 100"
        ),
        "ck_progress_seconds_spent_nonnegative": "`secondsSpent` >= 0",
    },
    "QuizResult": {
        "ck_quiz_result_score_range": "`score` >= 0 AND `score` <= 100",
        "ck_quiz_result_correct_count_nonnegative": "`correctCount` >= 0",
        "ck_quiz_result_total_count_positive": "`totalCount` > 0",
        "ck_quiz_result_correct_lte_total": "`correctCount` <= `totalCount`",
        "ck_quiz_result_attempt_number_positive": "`attemptNumber` > 0",
    },
}


@dataclass
class AuditReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _type_matches(actual: sa.types.TypeEngine[Any], kind: str, length: int | None) -> bool:
    if kind == "bool":
        return isinstance(actual, sa.Boolean) or (
            isinstance(actual, mysql.TINYINT)
            and getattr(actual, "display_width", None) in {None, 1}
        )
    if kind == "int":
        return isinstance(actual, sa.Integer) and not isinstance(actual, sa.Boolean)
    if kind == "str":
        return isinstance(actual, sa.String) and actual.length == length
    if kind == "text":
        return isinstance(actual, sa.Text)
    if kind == "datetime":
        return isinstance(actual, sa.DateTime)
    return False


def _is_current_timestamp_default(value: Any) -> bool:
    """Accept MySQL's equivalent spellings of the baseline ``now()`` default."""

    if value is None:
        return False
    normalised = re.sub(r"\s+", "", str(value)).lower()
    while normalised.startswith("(") and normalised.endswith(")"):
        depth = 0
        wraps_entire_expression = True
        for index, character in enumerate(normalised):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth < 0:
                    wraps_entire_expression = False
                    break
            if depth == 0 and index != len(normalised) - 1:
                wraps_entire_expression = False
                break
        if not wraps_entire_expression or depth != 0:
            break
        normalised = normalised[1:-1]
    return normalised in {"current_timestamp", "current_timestamp()", "now()"}


def _normalise_ondelete(value: Any) -> str:
    return str(value or "").upper().replace("_", " ")


def _audit_server_version(connection: Connection, report: AuditReport) -> None:
    dialect = connection.dialect
    if dialect.name not in {"mysql", "mariadb"}:
        report.errors.append(
            f"Expected MySQL/MariaDB, connected dialect is {dialect.name!r}"
        )
        return

    version = tuple(dialect.server_version_info or ())
    is_mariadb = dialect.name == "mariadb" or bool(
        getattr(dialect, "is_mariadb", False)
    )
    minimum = (10, 2, 1) if is_mariadb else (8, 0, 16)
    if not version or version < minimum:
        product = "MariaDB" if is_mariadb else "MySQL"
        report.errors.append(
            f"{product} {'.'.join(map(str, minimum))}+ is required for enforced "
            f"CHECK constraints; detected {version or 'unknown'}"
        )
    else:
        report.notes.append(
            f"Server supports enforced CHECK constraints: {version}"
        )


def _audit_version_table(
    connection: Connection,
    inspector: sa.Inspector,
    report: AuditReport,
    require_unversioned: bool,
) -> set[str]:
    if not inspector.has_table("alembic_version"):
        report.notes.append("No alembic_version table found (unversioned database)")
        return set()

    versions = list(
        connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars()
    )
    report.notes.append(f"Existing Alembic revision(s): {versions or ['<empty>']}")
    if require_unversioned:
        report.errors.append(
            "--require-unversioned was requested, but alembic_version already exists"
        )
    known = {"20261004_0001", "20261004_0002"}
    unknown = set(versions) - known
    if len(versions) != 1 or unknown:
        report.errors.append(
            f"Unexpected Alembic revision state: {versions}; expected one of {sorted(known)}"
        )
    return set(versions)


def _resolve_managed_table_names(
    connection: Connection,
    inspector: sa.Inspector,
    report: AuditReport,
) -> dict[str, str]:
    """Map canonical model names to reflected physical names.

    MySQL on Windows commonly enforces ``lower_case_table_names=1`` and reflects
    ``Parent`` as ``parent``. That is compatible with the unchanged CamelCase
    production DDL. Case folding is accepted only when the server confirms this
    mode; case-sensitive servers still require exact names.
    """

    lower_case_mode = int(
        connection.execute(sa.text("SELECT @@lower_case_table_names")).scalar_one()
    )
    actual_tables = set(inspector.get_table_names())
    managed_tables = set(EXPECTED_COLUMNS)
    resolved: dict[str, str] = {}

    if lower_case_mode:
        by_lower: dict[str, list[str]] = {}
        for actual_name in actual_tables:
            by_lower.setdefault(actual_name.lower(), []).append(actual_name)
        ambiguous = {
            key: names for key, names in by_lower.items() if len(names) > 1
        }
        if ambiguous:
            report.errors.append(
                f"Ambiguous case-folded table names: {ambiguous}"
            )
        for canonical in managed_tables:
            matches = by_lower.get(canonical.lower(), [])
            if len(matches) == 1:
                resolved[canonical] = matches[0]
        report.notes.append(
            f"lower_case_table_names={lower_case_mode}; accepted case-folded "
            "physical names while retaining canonical CamelCase model names"
        )
        managed_keys = {name.lower() for name in managed_tables}
        extras = {
            name
            for name in actual_tables
            if name.lower() not in managed_keys | {"alembic_version"}
        }
    else:
        resolved = {
            canonical: canonical
            for canonical in managed_tables
            if canonical in actual_tables
        }
        extras = actual_tables - managed_tables - {"alembic_version"}

    missing = managed_tables - set(resolved)
    if missing:
        report.errors.append(f"Missing managed tables: {sorted(missing)}")

    if extras:
        report.warnings.append(
            "Unmanaged extra tables require team confirmation and remain outside "
            f"this baseline: {sorted(extras)}"
        )

    return resolved


def _audit_table_structure(
    inspector: sa.Inspector,
    report: AuditReport,
    table_names: dict[str, str],
) -> bool:
    canonical_by_lower = {name.lower(): name for name in EXPECTED_COLUMNS}

    for table_name in sorted(table_names):
        physical_name = table_names[table_name]
        expected = EXPECTED_COLUMNS[table_name]
        actual_columns = {
            column["name"]: column for column in inspector.get_columns(physical_name)
        }
        expected_names = set(expected)
        actual_names = set(actual_columns)
        if expected_names != actual_names:
            report.errors.append(
                f"{table_name} columns differ; missing={sorted(expected_names - actual_names)}, "
                f"extra={sorted(actual_names - expected_names)}"
            )
            continue

        for column_name, (kind, length, nullable) in expected.items():
            actual = actual_columns[column_name]
            if bool(actual["nullable"]) != nullable:
                report.errors.append(
                    f"{table_name}.{column_name} nullable={actual['nullable']}; "
                    f"expected {nullable}"
                )
            if not _type_matches(actual["type"], kind, length):
                report.errors.append(
                    f"{table_name}.{column_name} type={actual['type']}; "
                    f"expected {kind}{f'({length})' if length else ''}"
                )
            if (
                (table_name, column_name) in REQUIRED_SERVER_DEFAULTS
                and not _is_current_timestamp_default(actual.get("default"))
            ):
                report.errors.append(
                    f"{table_name}.{column_name} default={actual.get('default')!r}; "
                    "expected CURRENT_TIMESTAMP/now()"
                )

        primary_key = tuple(
            inspector.get_pk_constraint(physical_name)["constrained_columns"]
        )
        if primary_key != EXPECTED_PRIMARY_KEYS[table_name]:
            report.errors.append(
                f"{table_name} primary key={primary_key}; "
                f"expected {EXPECTED_PRIMARY_KEYS[table_name]}"
            )
        for primary_key_column in EXPECTED_PRIMARY_KEYS[table_name]:
            if actual_columns[primary_key_column].get("autoincrement") is not True:
                report.errors.append(
                    f"{table_name}.{primary_key_column} is not AUTO_INCREMENT"
                )

        actual_foreign_keys: set[tuple[str, str, str, str]] = set()
        for foreign_key in inspector.get_foreign_keys(physical_name):
            local_columns = foreign_key.get("constrained_columns") or []
            remote_columns = foreign_key.get("referred_columns") or []
            if len(local_columns) == len(remote_columns) == 1:
                actual_foreign_keys.add(
                    (
                        local_columns[0],
                        canonical_by_lower.get(
                            str(foreign_key.get("referred_table")).lower(),
                            str(foreign_key.get("referred_table")),
                        ),
                        remote_columns[0],
                        _normalise_ondelete(
                            (foreign_key.get("options") or {}).get("ondelete")
                        ),
                    )
                )
            else:
                report.errors.append(
                    f"{table_name} has unsupported composite/malformed foreign key "
                    f"{foreign_key.get('name') or '<unnamed>'}: "
                    f"local={local_columns}, remote={remote_columns}"
                )
        if actual_foreign_keys != EXPECTED_FOREIGN_KEYS[table_name]:
            report.errors.append(
                f"{table_name} foreign keys={sorted(actual_foreign_keys)}; "
                f"expected {sorted(EXPECTED_FOREIGN_KEYS[table_name])}"
            )

        unique_sets = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints(physical_name)
            if item.get("column_names")
        }
        unique_sets.update(
            tuple(item["column_names"])
            for item in inspector.get_indexes(physical_name)
            if item.get("unique") and item.get("column_names")
        )
        expected_uniques = EXPECTED_UNIQUES.get(table_name, set())
        missing_uniques = expected_uniques - unique_sets
        extra_uniques = unique_sets - expected_uniques
        if missing_uniques:
            report.errors.append(
                f"{table_name} is missing unique key(s): {sorted(missing_uniques)}"
            )
        if extra_uniques:
            report.errors.append(
                f"{table_name} has unexpected unique key(s) that change baseline "
                f"semantics: {sorted(extra_uniques)}"
            )

        indexes = {
            tuple(item["column_names"])
            for item in inspector.get_indexes(physical_name)
            if item.get("column_names") and not item.get("unique")
        }
        expected_indexes = EXPECTED_INDEXES.get(table_name, set())
        missing_indexes = expected_indexes - indexes
        extra_indexes = indexes - expected_indexes
        if missing_indexes:
            report.errors.append(
                f"{table_name} is missing index(es): {sorted(missing_indexes)}"
            )
        if extra_indexes:
            report.warnings.append(
                f"{table_name} has extra non-unique index(es), which do not change "
                f"row validity but require operator review: {sorted(extra_indexes)}"
            )

    return len(table_names) == len(EXPECTED_COLUMNS) and not report.errors


def _normalise_check_sql(sqltext: str) -> str:
    return re.sub(r"[\s`()\"']+", "", sqltext).lower()


def _audit_check_constraints(
    inspector: sa.Inspector,
    report: AuditReport,
    table_names: dict[str, str],
    *,
    require_all: bool,
) -> None:
    for canonical_name in EXPECTED_COLUMNS:
        expected_checks = EXPECTED_CHECK_SQL.get(canonical_name, {})
        physical_name = table_names.get(canonical_name)
        if physical_name is None:
            continue
        reflected_checks = inspector.get_check_constraints(physical_name)
        unnamed_checks = [
            str(item.get("sqltext") or "")
            for item in reflected_checks
            if not item.get("name")
        ]
        if unnamed_checks:
            report.errors.append(
                f"{canonical_name} has unexpected unnamed CHECK constraint(s): "
                f"{unnamed_checks}"
            )
        actual_checks = {
            str(item["name"]).lower(): str(item.get("sqltext") or "")
            for item in reflected_checks
            if item.get("name")
        }
        required_checks = expected_checks if require_all else {}
        for constraint_name, expected_sql in required_checks.items():
            actual_sql = actual_checks.get(constraint_name.lower())
            if actual_sql is None:
                report.errors.append(
                    f"{canonical_name} is missing hardened constraint "
                    f"{constraint_name}"
                )
                continue
            if _normalise_check_sql(actual_sql) != _normalise_check_sql(expected_sql):
                report.errors.append(
                    f"{canonical_name}.{constraint_name} has definition "
                    f"{actual_sql!r}; expected {expected_sql!r}"
                )
        expected_names = {name.lower() for name in required_checks}
        extra_names = sorted(set(actual_checks) - expected_names)
        if extra_names:
            report.errors.append(
                f"{canonical_name} has unexpected CHECK constraint(s) that change "
                f"baseline semantics: {extra_names}"
            )


def _audit_data(
    connection: Connection,
    report: AuditReport,
    table_names: dict[str, str],
) -> None:
    for constraint_name, table_name, predicate in INVALID_DATA_PREDICATES:
        physical_name = table_names[table_name]
        count = connection.execute(
            sa.text(
                f"SELECT COUNT(*) FROM `{physical_name}` WHERE {predicate}"  # noqa: S608
            )
        ).scalar_one()
        if count:
            report.errors.append(
                f"{constraint_name} would reject {count} existing row(s) in {table_name}"
            )

    parent_table = table_names["Parent"]
    email_collisions = connection.execute(
        sa.text(
            f"SELECT COUNT(*) FROM ("  # noqa: S608
            f"SELECT 1 FROM `{parent_table}` "
            "GROUP BY (CONVERT(`email` USING utf8mb4) "
            "COLLATE utf8mb4_unicode_ci) "
            "HAVING COUNT(*) > 1"
            ") AS target_collation_email_collisions"
        )
    ).scalar_one()
    if email_collisions:
        report.errors.append(
            "Parent.email has "
            f"{email_collisions} colliding value group(s) under the target "
            "utf8mb4_unicode_ci collation"
        )


def _audit_collations(
    connection: Connection,
    report: AuditReport,
    table_names: dict[str, str],
) -> None:
    rows = connection.execute(
        sa.text(
            "SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE()"
        )
    )
    collations = {row[0]: row[1] for row in rows}
    conversions = {
        canonical: collations.get(physical_name)
        for canonical, physical_name in table_names.items()
        if collations.get(physical_name) != "utf8mb4_unicode_ci"
    }
    if conversions:
        report.warnings.append(
            "Hardening will rebuild/convert these table collations to "
            f"utf8mb4_unicode_ci: {conversions}"
        )
    else:
        report.notes.append("All managed tables already use utf8mb4_unicode_ci")


def audit_connection(
    connection: Connection,
    *,
    require_unversioned: bool = False,
) -> AuditReport:
    report = AuditReport()
    inspector = sa.inspect(connection)
    _audit_server_version(connection, report)
    versions = _audit_version_table(
        connection,
        inspector,
        report,
        require_unversioned,
    )
    table_names = _resolve_managed_table_names(connection, inspector, report)
    structure_ok = _audit_table_structure(inspector, report, table_names)
    _audit_check_constraints(
        inspector,
        report,
        table_names,
        require_all="20261004_0002" in versions,
    )
    if structure_ok:
        _audit_data(connection, report, table_names)
        _audit_collations(connection, report, table_names)
    else:
        report.warnings.append(
            "Data and collation checks were skipped because the baseline schema "
            "did not match"
        )
    return report


def _print_report(report: AuditReport) -> None:
    for note in report.notes:
        print(f"NOTE: {note}")
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    print("AUDIT PASS" if report.ok else "AUDIT FAIL")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-unversioned",
        action="store_true",
        help="fail if an alembic_version table already exists",
    )
    args = parser.parse_args(argv)

    engine = sa.create_engine(
        settings.database_url,
        connect_args=settings.database_connect_args,
        poolclass=NullPool,
    )
    try:
        with engine.connect() as connection:
            report = audit_connection(
                connection,
                require_unversioned=args.require_unversioned,
            )
    except sa.exc.SQLAlchemyError as exc:
        print(f"ERROR: read-only database audit failed: {exc}")
        return 2
    finally:
        engine.dispose()

    _print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
