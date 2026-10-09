"""Load demonstration data into a strictly local development/test database.

Running without flags never drops tables: it only seeds an empty database that
is already at Alembic head. ``--reset`` is destructive and additionally needs
two explicit confirmations. Every mode rejects remote hosts and ambiguous
database names, using the final URL parsed by ``Settings`` as the authority.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import sqlalchemy as sa
from sqlalchemy.engine import Connection, URL
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.security import hash_password
from backend.app.database import Base, SessionLocal, engine
from backend.app.models import (
    AudioResource,
    ChildProfile,
    LearningContent,
    LearningLevel,
    Lesson,
    Parent,
    Progress,
    Quiz,
    QuizOption,
    QuizQuestion,
    QuizResult,
)


BACKEND_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
LOCAL_DATABASE_HOSTS = {"localhost", "127.0.0.1", "::1"}
SAFE_DATABASE_NAME = re.compile(
    r"(?:^|[_-])(?:dev|test)(?:$|[_-])",
    re.IGNORECASE,
)
SAFE_APP_ENVS = {"development", "test"}


class SeedSafetyError(RuntimeError):
    """Raised before a database write when the configured target is unsafe."""


def seed_safety_errors(
    *,
    app_env: str,
    database_url: URL,
    reset: bool = False,
    confirm_database: str | None = None,
    yes_really_reset: bool = False,
) -> list[str]:
    """Return all safety failures for the already-parsed database target."""

    errors: list[str] = []
    target_host = (database_url.host or "").strip().lower().strip("[]")
    target_database = (database_url.database or "").strip()

    if app_env.strip().lower() not in SAFE_APP_ENVS:
        errors.append("APP_ENV must be exactly 'development' or 'test'")
    if target_host not in LOCAL_DATABASE_HOSTS:
        errors.append(
            "the parsed database URL host must be localhost, 127.0.0.1, or ::1"
        )
    if not SAFE_DATABASE_NAME.search(target_database):
        errors.append(
            "the parsed database name must contain a separate 'dev' or 'test' "
            "marker (for example coseat18_dev or coseat18-test)"
        )

    if reset:
        if confirm_database != target_database:
            errors.append(
                "--confirm-database must exactly match the parsed database name"
            )
        if not yes_really_reset:
            errors.append("--yes-really-reset is required with --reset")

    return errors


def validate_seed_target(
    *,
    reset: bool = False,
    confirm_database: str | None = None,
    yes_really_reset: bool = False,
) -> None:
    errors = seed_safety_errors(
        app_env=settings.APP_ENV,
        database_url=settings.database_url,
        reset=reset,
        confirm_database=confirm_database,
        yes_really_reset=yes_really_reset,
    )
    if errors:
        raise SeedSafetyError("Seed refused:\n - " + "\n - ".join(errors))


def _alembic_config(connection: Connection | None = None) -> Config:
    config = Config(str(ALEMBIC_INI))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def _head_revision() -> str:
    head = ScriptDirectory.from_config(_alembic_config()).get_current_head()
    if head is None:
        raise SeedSafetyError("Alembic has no head revision")
    return head


def _current_revision(connection: Connection) -> str | None:
    inspector = sa.inspect(connection)
    if not inspector.has_table("alembic_version"):
        return None
    revisions = list(
        connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalars()
    )
    if len(revisions) != 1:
        raise SeedSafetyError(
            f"Expected one Alembic revision row, found {len(revisions)}"
        )
    return revisions[0]


def _require_head_revision(connection: Connection) -> None:
    current = _current_revision(connection)
    head = _head_revision()
    if current != head:
        raise SeedSafetyError(
            f"Database revision is {current or '<unversioned>'}; expected {head}. "
            "Run 'alembic -c backend/alembic.ini upgrade head' first."
        )


def _require_managed_tables_empty(connection: Connection) -> None:
    inspector = sa.inspect(connection)
    missing = [
        table.name
        for table in Base.metadata.sorted_tables
        if not inspector.has_table(table.name)
    ]
    if missing:
        raise SeedSafetyError(f"Managed tables are missing: {missing}")

    populated: dict[str, int] = {}
    for table in Base.metadata.sorted_tables:
        count = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM `{table.name}`")  # noqa: S608
        ).scalar_one()
        if count:
            populated[table.name] = count
    if populated:
        raise SeedSafetyError(
            "Seed-only mode requires empty managed tables; found rows in "
            f"{populated}. Use a separately confirmed local --reset if intended."
        )


def _prepare_demo_password_hash(demo_password: str) -> str:
    """Validate and hash the demo password before any destructive reset DDL."""

    if not isinstance(demo_password, str) or len(demo_password) < 12:
        raise SeedSafetyError("DEMO_PARENT_PASSWORD must be at least 12 characters")
    try:
        return hash_password(demo_password)
    except (TypeError, UnicodeError, ValueError) as exc:
        raise SeedSafetyError(f"Invalid DEMO_PARENT_PASSWORD: {exc}") from exc


def _require_no_external_foreign_keys(connection: Connection) -> None:
    """Refuse reset if an unmanaged table depends on a managed table.

    Without this preflight, MySQL could commit several child-table drops and
    only then reject a parent-table drop, leaving a partially reset schema.
    """

    inspector = sa.inspect(connection)
    managed_names = {table.name.lower() for table in Base.metadata.sorted_tables}
    blockers: list[str] = []
    for table_name in inspector.get_table_names():
        if table_name.lower() in managed_names | {"alembic_version"}:
            continue
        for foreign_key in inspector.get_foreign_keys(table_name):
            referred_table = str(foreign_key.get("referred_table") or "")
            if referred_table.lower() in managed_names:
                constraint_name = foreign_key.get("name") or "<unnamed>"
                blockers.append(
                    f"{table_name}.{constraint_name} -> {referred_table}"
                )
    if blockers:
        raise SeedSafetyError(
            "Reset refused because unmanaged table foreign keys reference "
            f"managed tables: {sorted(blockers)}"
        )


def _reset_schema_to_head() -> None:
    """Drop only managed tables, then recreate them through Alembic.

    ``drop_all`` uses dependency order, so foreign-key checks remain enabled.
    The drop and migration use one connection; no shared/remote target can pass
    the safety gate that calls this function.
    """

    with engine.connect() as connection:
        _require_no_external_foreign_keys(connection)
        Base.metadata.drop_all(bind=connection, checkfirst=True)
        connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
        connection.commit()
        command.upgrade(_alembic_config(connection), "head")


def seed_demo_data(db: Session, *, password_hash: str) -> None:
    """Add the fixed demo dataset to the caller-owned transaction."""

    db.add_all(
        [
            LearningLevel(
                levelID=1,
                levelOrder=1,
                title="Beginner",
                description="Letters and basic sounds",
            ),
            LearningLevel(
                levelID=2,
                levelOrder=2,
                title="Intermediate",
                description="Vowel signs and simple words",
            ),
            LearningLevel(
                levelID=3,
                levelOrder=3,
                title="Advanced",
                description="Sentences and cultural reading",
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            Parent(
                parentID=1,
                email="demo@example.com",
                passwordHash=password_hash,
                displayName="Demo Parent",
                isAdmin=True,
            ),
            Parent(
                parentID=2,
                email="parent2@example.com",
                passwordHash=password_hash,
                displayName="Second Parent",
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            ChildProfile(
                childID=1,
                parentID=1,
                nickname="Rafi",
                ageBand="junior",
                currentLevelID=1,
            ),
            ChildProfile(
                childID=2,
                parentID=1,
                nickname="Mira",
                ageBand="senior",
                currentLevelID=2,
            ),
            ChildProfile(
                childID=3,
                parentID=2,
                nickname="Other Child",
                ageBand="junior",
                currentLevelID=1,
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            Lesson(
                lessonID=1,
                levelID=1,
                strand="letters",
                lessonOrder=1,
                title="Vowel letters",
                summary="First group of Bangla vowels",
                estimatedMinutes=5,
            ),
            Lesson(
                lessonID=2,
                levelID=1,
                strand="letters",
                lessonOrder=2,
                title="Consonant letters",
                summary="First group of Bangla consonants",
                estimatedMinutes=6,
            ),
            Lesson(
                lessonID=3,
                levelID=2,
                strand="letters",
                lessonOrder=1,
                title="Vowel signs",
                summary="How vowel signs change a consonant",
                estimatedMinutes=6,
            ),
            Lesson(
                lessonID=4,
                levelID=1,
                strand="culture",
                lessonOrder=1,
                title="Festivals",
                summary="Major festivals in Bangladesh",
                estimatedMinutes=5,
            ),
            Lesson(
                lessonID=5,
                levelID=2,
                strand="culture",
                lessonOrder=1,
                title="Rivers and land",
                summary="Rivers that shape the country",
                estimatedMinutes=6,
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            LearningContent(
                contentID=1,
                lessonID=1,
                blockOrder=1,
                blockKind="heading",
                textContent="The first vowels",
            ),
            LearningContent(
                contentID=2,
                lessonID=1,
                blockOrder=2,
                blockKind="prose",
                textContent=(
                    "Bangla vowels have their own shape and a matching sound."
                ),
            ),
            LearningContent(
                contentID=3,
                lessonID=1,
                blockOrder=3,
                blockKind="letter",
                textContent="First vowel",
                banglaText="অ",
                caption="Sounds like the o in son",
            ),
            LearningContent(
                contentID=4,
                lessonID=1,
                blockOrder=4,
                blockKind="letter",
                textContent="Second vowel",
                banglaText="আ",
                caption="Sounds like the a in father",
            ),
            LearningContent(
                contentID=5,
                lessonID=4,
                blockOrder=1,
                blockKind="heading",
                textContent="Festivals through the year",
            ),
            LearningContent(
                contentID=6,
                lessonID=4,
                blockOrder=2,
                blockKind="prose",
                textContent="Festival content is supplied by the content pipeline.",
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            AudioResource(
                audioID=1,
                lessonID=1,
                contentID=3,
                label="Vowel one",
                filePath="audio/letters/vowel-01.mp3",
            ),
            AudioResource(
                audioID=2,
                lessonID=1,
                contentID=4,
                label="Vowel two",
                filePath="audio/letters/vowel-02.mp3",
            ),
            AudioResource(
                audioID=3,
                lessonID=4,
                label="Festivals narration",
                filePath="audio/culture/festivals.mp3",
            ),
        ]
    )
    db.add_all(
        [
            Quiz(quizID=1, lessonID=1, title="Vowel letters check"),
            Quiz(quizID=2, lessonID=4, title="Festivals check"),
        ]
    )
    db.flush()

    db.add_all(
        [
            QuizQuestion(
                questionID=1,
                quizID=1,
                questionOrder=1,
                questionKind="single",
                prompt="Which letter sounds like the a in father?",
            ),
            QuizQuestion(
                questionID=2,
                quizID=1,
                questionOrder=2,
                questionKind="boolean",
                prompt="Bangla vowels can appear on their own.",
            ),
            QuizQuestion(
                questionID=3,
                quizID=2,
                questionOrder=1,
                questionKind="single",
                prompt="Which festival question placeholder?",
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            QuizOption(questionID=1, optionOrder=1, optionText="অ", isCorrect=False),
            QuizOption(questionID=1, optionOrder=2, optionText="আ", isCorrect=True),
            QuizOption(questionID=1, optionOrder=3, optionText="ই", isCorrect=False),
            QuizOption(
                questionID=2,
                optionOrder=1,
                optionText="True",
                isCorrect=True,
            ),
            QuizOption(
                questionID=2,
                optionOrder=2,
                optionText="False",
                isCorrect=False,
            ),
            QuizOption(
                questionID=3,
                optionOrder=1,
                optionText="First option",
                isCorrect=True,
            ),
            QuizOption(
                questionID=3,
                optionOrder=2,
                optionText="Second option",
                isCorrect=False,
            ),
        ]
    )
    db.add_all(
        [
            Progress(
                childID=1,
                lessonID=1,
                percentComplete=100,
                completed=True,
                secondsSpent=320,
            ),
            Progress(
                childID=1,
                lessonID=2,
                percentComplete=45,
                completed=False,
                secondsSpent=140,
            ),
            Progress(
                childID=2,
                lessonID=4,
                percentComplete=100,
                completed=True,
                secondsSpent=280,
            ),
        ]
    )
    db.add_all(
        [
            QuizResult(
                childID=1,
                quizID=1,
                score=100,
                correctCount=2,
                totalCount=2,
                passed=True,
            ),
            QuizResult(
                childID=2,
                quizID=2,
                score=100,
                correctCount=1,
                totalCount=1,
                passed=True,
            ),
        ]
    )
    db.flush()


def _seed_empty_database(*, password_hash: str) -> None:
    db = SessionLocal()
    try:
        connection = db.connection()
        _require_head_revision(connection)
        _require_managed_tables_empty(connection)
        seed_demo_data(db, password_hash=password_hash)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="drop managed local tables, migrate to head, then seed",
    )
    parser.add_argument(
        "--confirm-database",
        metavar="DB_NAME",
        help="first reset confirmation: must exactly match the parsed DB name",
    )
    parser.add_argument(
        "--yes-really-reset",
        action="store_true",
        help="second reset confirmation",
    )
    args = parser.parse_args(argv)

    try:
        validate_seed_target(
            reset=args.reset,
            confirm_database=args.confirm_database,
            yes_really_reset=args.yes_really_reset,
        )
        demo_password = os.getenv("DEMO_PARENT_PASSWORD", "local-demo-password")
        password_hash = _prepare_demo_password_hash(demo_password)
        if args.reset:
            _reset_schema_to_head()
        _seed_empty_database(password_hash=password_hash)
    except SeedSafetyError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("Local demo data loaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
