"""Freeze the original eleven-table schema.

Revision ID: 20261004_0001
Revises:
Create Date: 2026-10-04

This revision intentionally mirrors the pre-migration schema. Integrity checks
and explicit utf8mb4 table options belong to the following revision.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20261004_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "LearningLevel",
        sa.Column("levelID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("levelOrder", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("passMark", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("levelID"),
        sa.UniqueConstraint("levelOrder"),
    )
    op.create_table(
        "Parent",
        sa.Column("parentID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("passwordHash", sa.String(length=255), nullable=False),
        sa.Column("displayName", sa.String(length=100), nullable=False),
        sa.Column("pinHash", sa.String(length=255), nullable=True),
        sa.Column("otpCode", sa.String(length=10), nullable=True),
        sa.Column("otpExpiresAt", sa.DateTime(), nullable=True),
        sa.Column("isAdmin", sa.Boolean(), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("parentID"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "ChildProfile",
        sa.Column("childID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parentID", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(length=60), nullable=False),
        sa.Column("avatar", sa.String(length=150), nullable=True),
        sa.Column("ageBand", sa.String(length=20), nullable=False),
        sa.Column("currentLevelID", sa.Integer(), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["currentLevelID"],
            ["LearningLevel.levelID"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parentID"],
            ["Parent.parentID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("childID"),
    )
    op.create_index(
        "ix_ChildProfile_currentLevelID",
        "ChildProfile",
        ["currentLevelID"],
        unique=False,
    )
    op.create_index(
        "ix_ChildProfile_parentID",
        "ChildProfile",
        ["parentID"],
        unique=False,
    )
    op.create_table(
        "Lesson",
        sa.Column("lessonID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("levelID", sa.Integer(), nullable=False),
        sa.Column("strand", sa.String(length=20), nullable=False),
        sa.Column("lessonOrder", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("coverImage", sa.String(length=150), nullable=True),
        sa.Column("estimatedMinutes", sa.Integer(), nullable=False),
        sa.Column("isPublished", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["levelID"],
            ["LearningLevel.levelID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("lessonID"),
    )
    op.create_index("ix_Lesson_levelID", "Lesson", ["levelID"], unique=False)
    op.create_index("ix_Lesson_strand", "Lesson", ["strand"], unique=False)
    op.create_table(
        "LearningContent",
        sa.Column("contentID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lessonID", sa.Integer(), nullable=False),
        sa.Column("blockOrder", sa.Integer(), nullable=False),
        sa.Column("blockKind", sa.String(length=20), nullable=False),
        sa.Column("textContent", sa.Text(), nullable=True),
        sa.Column("banglaText", sa.Text(), nullable=True),
        sa.Column("mediaPath", sa.String(length=150), nullable=True),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["lessonID"],
            ["Lesson.lessonID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("contentID"),
    )
    op.create_index(
        "ix_LearningContent_lessonID",
        "LearningContent",
        ["lessonID"],
        unique=False,
    )
    op.create_table(
        "AudioResource",
        sa.Column("audioID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lessonID", sa.Integer(), nullable=True),
        sa.Column("contentID", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("filePath", sa.String(length=200), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["contentID"],
            ["LearningContent.contentID"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lessonID"],
            ["Lesson.lessonID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("audioID"),
    )
    op.create_index(
        "ix_AudioResource_contentID",
        "AudioResource",
        ["contentID"],
        unique=False,
    )
    op.create_index(
        "ix_AudioResource_lessonID",
        "AudioResource",
        ["lessonID"],
        unique=False,
    )
    op.create_table(
        "Quiz",
        sa.Column("quizID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lessonID", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("passMark", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lessonID"],
            ["Lesson.lessonID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("quizID"),
    )
    op.create_index("ix_Quiz_lessonID", "Quiz", ["lessonID"], unique=False)
    op.create_table(
        "QuizQuestion",
        sa.Column("questionID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quizID", sa.Integer(), nullable=False),
        sa.Column("questionOrder", sa.Integer(), nullable=False),
        sa.Column("questionKind", sa.String(length=20), nullable=False),
        sa.Column("prompt", sa.String(length=255), nullable=False),
        sa.Column("mediaPath", sa.String(length=150), nullable=True),
        sa.ForeignKeyConstraint(
            ["quizID"],
            ["Quiz.quizID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("questionID"),
    )
    op.create_index(
        "ix_QuizQuestion_quizID",
        "QuizQuestion",
        ["quizID"],
        unique=False,
    )
    op.create_table(
        "QuizOption",
        sa.Column("optionID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("questionID", sa.Integer(), nullable=False),
        sa.Column("optionOrder", sa.Integer(), nullable=False),
        sa.Column("optionText", sa.String(length=255), nullable=False),
        sa.Column("isCorrect", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["questionID"],
            ["QuizQuestion.questionID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("optionID"),
    )
    op.create_index(
        "ix_QuizOption_questionID",
        "QuizOption",
        ["questionID"],
        unique=False,
    )
    op.create_table(
        "Progress",
        sa.Column("progressID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("childID", sa.Integer(), nullable=False),
        sa.Column("lessonID", sa.Integer(), nullable=False),
        sa.Column("percentComplete", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("secondsSpent", sa.Integer(), nullable=False),
        sa.Column(
            "lastViewedAt",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["childID"],
            ["ChildProfile.childID"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lessonID"],
            ["Lesson.lessonID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("progressID"),
        sa.UniqueConstraint(
            "childID",
            "lessonID",
            name="uq_progress_child_lesson",
        ),
    )
    op.create_index(
        "idx_progress_lesson",
        "Progress",
        ["lessonID"],
        unique=False,
    )
    op.create_table(
        "QuizResult",
        sa.Column("resultID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("childID", sa.Integer(), nullable=False),
        sa.Column("quizID", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("correctCount", sa.Integer(), nullable=False),
        sa.Column("totalCount", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("attemptNumber", sa.Integer(), nullable=False),
        sa.Column(
            "submittedAt",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["childID"],
            ["ChildProfile.childID"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["quizID"],
            ["Quiz.quizID"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("resultID"),
    )
    op.create_index(
        "ix_QuizResult_childID",
        "QuizResult",
        ["childID"],
        unique=False,
    )
    op.create_index(
        "ix_QuizResult_quizID",
        "QuizResult",
        ["quizID"],
        unique=False,
    )


def downgrade() -> None:
    # DROP TABLE removes its indexes too. Dropping FK-supporting indexes first
    # fails on InnoDB; remove tables in reverse dependency order instead.
    op.drop_table("QuizResult")
    op.drop_table("Progress")
    op.drop_table("QuizOption")
    op.drop_table("QuizQuestion")
    op.drop_table("Quiz")
    op.drop_table("AudioResource")
    op.drop_table("LearningContent")
    op.drop_table("Lesson")
    op.drop_table("ChildProfile")
    op.drop_table("Parent")
    op.drop_table("LearningLevel")
