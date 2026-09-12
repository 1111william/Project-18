import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import text

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


def reset_schema():
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


def seed():
    db = SessionLocal()
    try:
        demo_password = hash_password("password")

        db.add_all([
            LearningLevel(levelID=1, levelOrder=1, title="Beginner", description="Letters and basic sounds"),
            LearningLevel(levelID=2, levelOrder=2, title="Intermediate", description="Vowel signs and simple words"),
            LearningLevel(levelID=3, levelOrder=3, title="Advanced", description="Sentences and cultural reading"),
        ])
        db.flush()

        db.add_all([
            Parent(parentID=1, email="demo@example.com", passwordHash=demo_password, displayName="Demo Parent", isAdmin=True),
            Parent(parentID=2, email="parent2@example.com", passwordHash=demo_password, displayName="Second Parent"),
        ])
        db.flush()

        db.add_all([
            ChildProfile(childID=1, parentID=1, nickname="Rafi", ageBand="junior", currentLevelID=1),
            ChildProfile(childID=2, parentID=1, nickname="Mira", ageBand="senior", currentLevelID=2),
            ChildProfile(childID=3, parentID=2, nickname="Other Child", ageBand="junior", currentLevelID=1),
        ])
        db.flush()

        db.add_all([
            Lesson(lessonID=1, levelID=1, strand="letters", lessonOrder=1, title="Vowel letters", summary="First group of Bangla vowels", estimatedMinutes=5),
            Lesson(lessonID=2, levelID=1, strand="letters", lessonOrder=2, title="Consonant letters", summary="First group of Bangla consonants", estimatedMinutes=6),
            Lesson(lessonID=3, levelID=2, strand="letters", lessonOrder=1, title="Vowel signs", summary="How vowel signs change a consonant", estimatedMinutes=6),
            Lesson(lessonID=4, levelID=1, strand="culture", lessonOrder=1, title="Festivals", summary="Major festivals in Bangladesh", estimatedMinutes=5),
            Lesson(lessonID=5, levelID=2, strand="culture", lessonOrder=1, title="Rivers and land", summary="Rivers that shape the country", estimatedMinutes=6),
        ])
        db.flush()

        db.add_all([
            LearningContent(contentID=1, lessonID=1, blockOrder=1, blockKind="heading", textContent="The first vowels"),
            LearningContent(contentID=2, lessonID=1, blockOrder=2, blockKind="prose", textContent="Bangla vowels have their own shape and a matching sound."),
            LearningContent(contentID=3, lessonID=1, blockOrder=3, blockKind="letter", textContent="First vowel", banglaText="অ", caption="Sounds like the o in son"),
            LearningContent(contentID=4, lessonID=1, blockOrder=4, blockKind="letter", textContent="Second vowel", banglaText="আ", caption="Sounds like the a in father"),
            LearningContent(contentID=5, lessonID=4, blockOrder=1, blockKind="heading", textContent="Festivals through the year"),
            LearningContent(contentID=6, lessonID=4, blockOrder=2, blockKind="prose", textContent="Festival content is supplied by the content pipeline."),
        ])
        db.flush()

        db.add_all([
            AudioResource(audioID=1, lessonID=1, contentID=3, label="Vowel one", filePath="audio/letters/vowel-01.mp3"),
            AudioResource(audioID=2, lessonID=1, contentID=4, label="Vowel two", filePath="audio/letters/vowel-02.mp3"),
            AudioResource(audioID=3, lessonID=4, label="Festivals narration", filePath="audio/culture/festivals.mp3"),
        ])

        db.add_all([
            Quiz(quizID=1, lessonID=1, title="Vowel letters check"),
            Quiz(quizID=2, lessonID=4, title="Festivals check"),
        ])
        db.flush()

        db.add_all([
            QuizQuestion(questionID=1, quizID=1, questionOrder=1, questionKind="single", prompt="Which letter sounds like the a in father?"),
            QuizQuestion(questionID=2, quizID=1, questionOrder=2, questionKind="boolean", prompt="Bangla vowels can appear on their own."),
            QuizQuestion(questionID=3, quizID=2, questionOrder=1, questionKind="single", prompt="Which festival question placeholder?"),
        ])
        db.flush()

        db.add_all([
            QuizOption(questionID=1, optionOrder=1, optionText="অ", isCorrect=False),
            QuizOption(questionID=1, optionOrder=2, optionText="আ", isCorrect=True),
            QuizOption(questionID=1, optionOrder=3, optionText="ই", isCorrect=False),
            QuizOption(questionID=2, optionOrder=1, optionText="True", isCorrect=True),
            QuizOption(questionID=2, optionOrder=2, optionText="False", isCorrect=False),
            QuizOption(questionID=3, optionOrder=1, optionText="First option", isCorrect=True),
            QuizOption(questionID=3, optionOrder=2, optionText="Second option", isCorrect=False),
        ])

        db.add_all([
            Progress(childID=1, lessonID=1, percentComplete=100, completed=True, secondsSpent=320),
            Progress(childID=1, lessonID=2, percentComplete=45, completed=False, secondsSpent=140),
            Progress(childID=2, lessonID=4, percentComplete=100, completed=True, secondsSpent=280),
        ])

        db.add_all([
            QuizResult(childID=1, quizID=1, score=100, correctCount=2, totalCount=2, passed=True),
            QuizResult(childID=2, quizID=2, score=50, correctCount=1, totalCount=2, passed=False),
        ])

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    reset_schema()
    seed()
    print("Schema created and seed data loaded")
