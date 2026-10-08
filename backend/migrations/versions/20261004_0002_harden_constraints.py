"""Add objective integrity checks and explicit utf8mb4 storage.

Revision ID: 20261004_0002
Revises: 20261004_0001
Create Date: 2026-10-04

MySQL DDL auto-commits. This migration performs all data checks before its first
DDL statement and skips already-present named checks so a reviewed retry can
continue after a partial infrastructure failure.
"""

from collections.abc import Sequence
import re

from alembic import op
import sqlalchemy as sa


revision: str = "20261004_0002"
down_revision: str | Sequence[str] | None = "20261004_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLES = (
    "Parent",
    "LearningLevel",
    "ChildProfile",
    "Lesson",
    "LearningContent",
    "AudioResource",
    "Quiz",
    "QuizQuestion",
    "QuizOption",
    "Progress",
    "QuizResult",
)

CHECKS: dict[str, tuple[tuple[str, str], ...]] = {
    "LearningLevel": (
        ("ck_learning_level_order_positive", "`levelOrder` > 0"),
        (
            "ck_learning_level_pass_mark_range",
            "`passMark` >= 0 AND `passMark` <= 100",
        ),
    ),
    "Lesson": (
        ("ck_lesson_order_positive", "`lessonOrder` > 0"),
        (
            "ck_lesson_estimated_minutes_nonnegative",
            "`estimatedMinutes` >= 0",
        ),
    ),
    "LearningContent": (
        (
            "ck_learning_content_block_order_positive",
            "`blockOrder` > 0",
        ),
    ),
    "Quiz": (
        (
            "ck_quiz_pass_mark_range",
            "`passMark` >= 0 AND `passMark` <= 100",
        ),
    ),
    "QuizQuestion": (
        ("ck_quiz_question_order_positive", "`questionOrder` > 0"),
    ),
    "QuizOption": (
        ("ck_quiz_option_order_positive", "`optionOrder` > 0"),
    ),
    "Progress": (
        (
            "ck_progress_percent_complete_range",
            "`percentComplete` >= 0 AND `percentComplete` <= 100",
        ),
        (
            "ck_progress_seconds_spent_nonnegative",
            "`secondsSpent` >= 0",
        ),
    ),
    "QuizResult": (
        (
            "ck_quiz_result_score_range",
            "`score` >= 0 AND `score` <= 100",
        ),
        (
            "ck_quiz_result_correct_count_nonnegative",
            "`correctCount` >= 0",
        ),
        ("ck_quiz_result_total_count_positive", "`totalCount` > 0"),
        (
            "ck_quiz_result_correct_lte_total",
            "`correctCount` <= `totalCount`",
        ),
        (
            "ck_quiz_result_attempt_number_positive",
            "`attemptNumber` > 0",
        ),
    ),
}

INVALID_DATA_PREDICATES: tuple[tuple[str, str, str], ...] = (
    (
        "ck_learning_level_order_positive",
        "LearningLevel",
        "`levelOrder` <= 0",
    ),
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


def _offline() -> bool:
    return bool(op.get_context().as_sql)


def _require_check_enforcement(bind: sa.engine.Connection) -> None:
    dialect = bind.dialect
    if dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("Database hardening supports MySQL/MariaDB only")

    version = dialect.server_version_info
    if not version:
        raise RuntimeError("Could not determine database server version")

    is_mariadb = dialect.name == "mariadb" or bool(
        getattr(dialect, "is_mariadb", False)
    )
    minimum = (10, 2, 1) if is_mariadb else (8, 0, 16)
    if tuple(version) < minimum:
        product = "MariaDB" if is_mariadb else "MySQL"
        required = ".".join(str(part) for part in minimum)
        actual = ".".join(str(part) for part in version)
        raise RuntimeError(
            f"{product} {required}+ is required for enforced CHECK constraints; "
            f"connected server is {actual}"
        )


def _assert_existing_data_is_valid(bind: sa.engine.Connection) -> None:
    failures: list[str] = []
    for constraint_name, table_name, predicate in INVALID_DATA_PREDICATES:
        count = bind.execute(
            sa.text(
                f"SELECT COUNT(*) FROM `{table_name}` WHERE {predicate}"  # noqa: S608
            )
        ).scalar_one()
        if count:
            failures.append(f"{constraint_name}: {count} violating row(s)")

    email_collisions = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM ("
            "SELECT 1 FROM `Parent` "
            "GROUP BY (CONVERT(`email` USING utf8mb4) "
            "COLLATE utf8mb4_unicode_ci) "
            "HAVING COUNT(*) > 1"
            ") AS target_collation_email_collisions"
        )
    ).scalar_one()
    if email_collisions:
        failures.append(
            "uq_parent_email_target_collation: "
            f"{email_collisions} colliding value group(s) under "
            "utf8mb4_unicode_ci"
        )

    if failures:
        joined = "\n - ".join(failures)
        raise RuntimeError(
            "Database hardening stopped before DDL because existing data violates "
            f"the proposed constraints:\n - {joined}\n"
            "Review and correct the data through the owning feature team; this "
            "migration will not clean or rewrite user data."
        )


def _normalise_check_sql(sqltext: str) -> str:
    """Normalise harmless reflection differences, not logical differences."""

    return re.sub(r"[\s`()\"']+", "", sqltext).lower()


def _reflected_checks(
    bind: sa.engine.Connection,
    table_name: str,
) -> dict[str, str]:
    return {
        str(row["name"]).lower(): str(row.get("sqltext") or "")
        for row in sa.inspect(bind).get_check_constraints(table_name)
        if row.get("name")
    }


def _assert_existing_checks_match(bind: sa.engine.Connection) -> None:
    failures: list[str] = []
    for table_name, checks in CHECKS.items():
        existing = _reflected_checks(bind, table_name)
        for constraint_name, expected_sql in checks:
            actual_sql = existing.get(constraint_name.lower())
            if actual_sql is not None and _normalise_check_sql(
                actual_sql
            ) != _normalise_check_sql(expected_sql):
                failures.append(
                    f"{table_name}.{constraint_name}: reflected {actual_sql!r}, "
                    f"expected {expected_sql!r}"
                )

    if failures:
        joined = "\n - ".join(failures)
        raise RuntimeError(
            "Database hardening found existing constraints with expected names "
            f"but different definitions; refusing to skip them:\n - {joined}"
        )


def _convert_tables_to_utf8mb4(bind: sa.engine.Connection | None) -> None:
    for table_name in TABLES:
        if bind is not None:
            current_collation = bind.execute(
                sa.text(
                    "SELECT TABLE_COLLATION FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "AND LOWER(TABLE_NAME) = LOWER(:table_name)"
                ),
                {"table_name": table_name},
            ).scalar_one_or_none()
            if current_collation == "utf8mb4_unicode_ci":
                continue
            if current_collation is None:
                raise RuntimeError(f"Required table is missing: {table_name}")

        op.execute(
            f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET utf8mb4 "
            "COLLATE utf8mb4_unicode_ci"
        )


def _create_checks(bind: sa.engine.Connection | None) -> None:
    for table_name, checks in CHECKS.items():
        existing: set[str] = set()
        if bind is not None:
            existing = set(_reflected_checks(bind, table_name))
        for constraint_name, condition in checks:
            if constraint_name.lower() not in existing:
                op.create_check_constraint(constraint_name, table_name, condition)


def upgrade() -> None:
    bind = None if _offline() else op.get_bind()
    if bind is not None:
        _require_check_enforcement(bind)
        _assert_existing_data_is_valid(bind)
        _assert_existing_checks_match(bind)

    _convert_tables_to_utf8mb4(bind)
    _create_checks(bind)


def downgrade() -> None:
    bind = None if _offline() else op.get_bind()
    for table_name, checks in reversed(tuple(CHECKS.items())):
        existing: set[str] | None = None
        if bind is not None:
            existing = {
                str(row["name"]).lower()
                for row in sa.inspect(bind).get_check_constraints(table_name)
                if row.get("name")
            }
        for constraint_name, _condition in reversed(checks):
            if existing is None or constraint_name.lower() in existing:
                op.drop_constraint(constraint_name, table_name, type_="check")

    # Character-set conversion is intentionally not reversed. The baseline did
    # not record a previous charset, and converting Unicode data back could be
    # lossy. Restore a backup if the storage conversion itself must be undone.
