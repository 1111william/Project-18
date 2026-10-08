from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


def _mysql_table_options() -> dict[str, str]:
    """Return consistent Unicode defaults without sharing a mutable dict."""

    return {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }


class Parent(Base):
    __tablename__ = "Parent"
    __table_args__ = _mysql_table_options()

    parentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    passwordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    displayName: Mapped[str] = mapped_column(String(100), nullable=False)
    pinHash: Mapped[str] = mapped_column(String(255), nullable=True)
    otpCode: Mapped[str] = mapped_column(String(10), nullable=True)
    otpExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    children: Mapped[list["ChildProfile"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )


class LearningLevel(Base):
    __tablename__ = "LearningLevel"
    __table_args__ = (
        CheckConstraint(
            "levelOrder > 0",
            name="ck_learning_level_order_positive",
        ),
        CheckConstraint(
            "passMark >= 0 AND passMark <= 100",
            name="ck_learning_level_pass_mark_range",
        ),
        _mysql_table_options(),
    )

    levelID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    levelOrder: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    passMark: Mapped[int] = mapped_column(Integer, nullable=False, default=70)

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="level",
        passive_deletes="all",
    )


class ChildProfile(Base):
    __tablename__ = "ChildProfile"
    __table_args__ = _mysql_table_options()

    childID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parentID: Mapped[int] = mapped_column(
        ForeignKey("Parent.parentID", ondelete="CASCADE"), nullable=False, index=True
    )
    nickname: Mapped[str] = mapped_column(String(60), nullable=False)
    avatar: Mapped[str] = mapped_column(String(150), nullable=True)
    ageBand: Mapped[str] = mapped_column(String(20), nullable=False, default="junior")
    currentLevelID: Mapped[int] = mapped_column(
        ForeignKey("LearningLevel.levelID", ondelete="SET NULL"), nullable=True, index=True
    )
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    parent: Mapped["Parent"] = relationship(back_populates="children")
    level: Mapped["LearningLevel"] = relationship()


class Lesson(Base):
    __tablename__ = "Lesson"
    __table_args__ = (
        CheckConstraint(
            "lessonOrder > 0",
            name="ck_lesson_order_positive",
        ),
        CheckConstraint(
            "estimatedMinutes >= 0",
            name="ck_lesson_estimated_minutes_nonnegative",
        ),
        _mysql_table_options(),
    )

    lessonID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    levelID: Mapped[int] = mapped_column(
        ForeignKey("LearningLevel.levelID", ondelete="CASCADE"), nullable=False, index=True
    )
    strand: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    lessonOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=True)
    coverImage: Mapped[str] = mapped_column(String(150), nullable=True)
    estimatedMinutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    isPublished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    level: Mapped["LearningLevel"] = relationship(back_populates="lessons")
    blocks: Mapped[list["LearningContent"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class LearningContent(Base):
    __tablename__ = "LearningContent"
    __table_args__ = (
        CheckConstraint(
            "blockOrder > 0",
            name="ck_learning_content_block_order_positive",
        ),
        _mysql_table_options(),
    )

    contentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lessonID: Mapped[int] = mapped_column(
        ForeignKey("Lesson.lessonID", ondelete="CASCADE"), nullable=False, index=True
    )
    blockOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    blockKind: Mapped[str] = mapped_column(String(20), nullable=False)
    textContent: Mapped[str] = mapped_column(Text, nullable=True)
    banglaText: Mapped[str] = mapped_column(Text, nullable=True)
    mediaPath: Mapped[str] = mapped_column(String(150), nullable=True)
    caption: Mapped[str] = mapped_column(String(255), nullable=True)

    lesson: Mapped["Lesson"] = relationship(back_populates="blocks")


class AudioResource(Base):
    __tablename__ = "AudioResource"
    __table_args__ = _mysql_table_options()

    audioID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lessonID: Mapped[int] = mapped_column(
        ForeignKey("Lesson.lessonID", ondelete="CASCADE"), nullable=True, index=True
    )
    contentID: Mapped[int] = mapped_column(
        ForeignKey("LearningContent.contentID", ondelete="CASCADE"), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    filePath: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="tts")
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Quiz(Base):
    __tablename__ = "Quiz"
    __table_args__ = (
        CheckConstraint(
            "passMark >= 0 AND passMark <= 100",
            name="ck_quiz_pass_mark_range",
        ),
        _mysql_table_options(),
    )

    quizID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lessonID: Mapped[int] = mapped_column(
        ForeignKey("Lesson.lessonID", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    passMark: Mapped[int] = mapped_column(Integer, nullable=False, default=70)

    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    __tablename__ = "QuizQuestion"
    __table_args__ = (
        CheckConstraint(
            "questionOrder > 0",
            name="ck_quiz_question_order_positive",
        ),
        _mysql_table_options(),
    )

    questionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quizID: Mapped[int] = mapped_column(
        ForeignKey("Quiz.quizID", ondelete="CASCADE"), nullable=False, index=True
    )
    questionOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    questionKind: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(String(255), nullable=False)
    mediaPath: Mapped[str] = mapped_column(String(150), nullable=True)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    options: Mapped[list["QuizOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class QuizOption(Base):
    __tablename__ = "QuizOption"
    __table_args__ = (
        CheckConstraint(
            "optionOrder > 0",
            name="ck_quiz_option_order_positive",
        ),
        _mysql_table_options(),
    )

    optionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    questionID: Mapped[int] = mapped_column(
        ForeignKey("QuizQuestion.questionID", ondelete="CASCADE"), nullable=False, index=True
    )
    optionOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    optionText: Mapped[str] = mapped_column(String(255), nullable=False)
    isCorrect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["QuizQuestion"] = relationship(back_populates="options")


class Progress(Base):
    __tablename__ = "Progress"
    __table_args__ = (
        UniqueConstraint("childID", "lessonID", name="uq_progress_child_lesson"),
        Index("idx_progress_lesson", "lessonID"),
        CheckConstraint(
            "percentComplete >= 0 AND percentComplete <= 100",
            name="ck_progress_percent_complete_range",
        ),
        CheckConstraint(
            "secondsSpent >= 0",
            name="ck_progress_seconds_spent_nonnegative",
        ),
        _mysql_table_options(),
    )

    progressID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    childID: Mapped[int] = mapped_column(
        ForeignKey("ChildProfile.childID", ondelete="CASCADE"), nullable=False
    )
    lessonID: Mapped[int] = mapped_column(
        ForeignKey("Lesson.lessonID", ondelete="CASCADE"), nullable=False
    )
    percentComplete: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    secondsSpent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lastViewedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class QuizResult(Base):
    __tablename__ = "QuizResult"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_quiz_result_score_range",
        ),
        CheckConstraint(
            "correctCount >= 0",
            name="ck_quiz_result_correct_count_nonnegative",
        ),
        CheckConstraint(
            "totalCount > 0",
            name="ck_quiz_result_total_count_positive",
        ),
        CheckConstraint(
            "correctCount <= totalCount",
            name="ck_quiz_result_correct_lte_total",
        ),
        CheckConstraint(
            "attemptNumber > 0",
            name="ck_quiz_result_attempt_number_positive",
        ),
        _mysql_table_options(),
    )

    resultID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    childID: Mapped[int] = mapped_column(
        ForeignKey("ChildProfile.childID", ondelete="CASCADE"), nullable=False, index=True
    )
    quizID: Mapped[int] = mapped_column(
        ForeignKey("Quiz.quizID", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    correctCount: Mapped[int] = mapped_column(Integer, nullable=False)
    totalCount: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attemptNumber: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    submittedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
