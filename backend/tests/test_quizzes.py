import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import (
    ChildProfile,
    LearningLevel,
    Lesson,
    Parent,
    Quiz,
    QuizOption,
    QuizQuestion,
    QuizResult,
)


@pytest.fixture
def env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all(
            [
                Parent(
                    parentID=parent_id,
                    email=f"{parent_id}@test.invalid",
                    passwordHash="unused",
                    displayName="Test",
                )
                for parent_id in (1, 2)
            ]
        )
        db.add(LearningLevel(levelID=1, levelOrder=1, title="Beginner"))
        db.flush()
        db.add_all(
            [
                ChildProfile(childID=1, parentID=1, nickname="First"),
                ChildProfile(childID=2, parentID=2, nickname="Second"),
            ]
        )
        db.add_all(
            [
                Lesson(
                    lessonID=1,
                    levelID=1,
                    strand="letters",
                    lessonOrder=1,
                    title="Letters",
                    isPublished=True,
                ),
                Lesson(
                    lessonID=2,
                    levelID=1,
                    strand="letters",
                    lessonOrder=2,
                    title="Draft",
                    isPublished=False,
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                Quiz(quizID=1, lessonID=1, title="বাংলা", passMark=70),
                Quiz(quizID=2, lessonID=1, title="Empty", passMark=70),
                Quiz(quizID=3, lessonID=2, title="Draft quiz", passMark=70),
            ]
        )
        db.flush()
        db.add_all(
            [
                QuizQuestion(
                    questionID=1,
                    quizID=1,
                    questionOrder=2,
                    questionKind="single",
                    prompt="Choose one",
                ),
                QuizQuestion(
                    questionID=2,
                    quizID=1,
                    questionOrder=1,
                    questionKind="multiple",
                    prompt="Choose two",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                QuizOption(
                    optionID=1,
                    questionID=1,
                    optionOrder=2,
                    optionText="অ",
                    isCorrect=False,
                ),
                QuizOption(
                    optionID=2,
                    questionID=1,
                    optionOrder=1,
                    optionText="আ",
                    isCorrect=True,
                ),
                QuizOption(
                    optionID=3,
                    questionID=2,
                    optionOrder=1,
                    optionText="ক",
                    isCorrect=True,
                ),
                QuizOption(
                    optionID=4,
                    questionID=2,
                    optionOrder=2,
                    optionText="খ",
                    isCorrect=True,
                ),
                QuizOption(
                    optionID=5,
                    questionID=2,
                    optionOrder=3,
                    optionText="গ",
                    isCorrect=False,
                ),
            ]
        )
        db.commit()

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    with TestClient(app, raise_server_exceptions=False) as client:
        payload = base64.b64encode(json.dumps({"parentID": 1}).encode())
        client.cookies.set(
            "session",
            TimestampSigner(settings.SESSION_SECRET).sign(payload).decode(),
        )
        client.headers["Origin"] = "http://testserver"
        yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def correct_answers():
    return {
        "answers": [
            {"questionID": 1, "selectedOptionIDs": [2]},
            {"questionID": 2, "selectedOptionIDs": [3, 4]},
        ]
    }


def submit(client, body=None, child=1, quiz=1):
    return client.post(
        f"/api/children/{child}/quizzes/{quiz}/attempts",
        json=correct_answers() if body is None else body,
    )


def test_list_quizzes_for_published_lesson(env):
    client, _ = env
    response = client.get("/api/quizzes?lessonID=1")
    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "quizID": 1,
            "lessonID": 1,
            "title": "বাংলা",
            "passMark": 70,
            "questionCount": 2,
        },
        {
            "quizID": 2,
            "lessonID": 1,
            "title": "Empty",
            "passMark": 70,
            "questionCount": 0,
        },
    ]
    assert client.get("/api/quizzes?lessonID=2").status_code == 404
    assert client.get("/api/quizzes?lessonID=999").status_code == 404


def test_quiz_detail_orders_content_without_leaking_answers(env):
    client, _ = env
    response = client.get("/api/quizzes/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "বাংলা"
    assert [item["questionID"] for item in data["questions"]] == [2, 1]
    assert [item["optionID"] for item in data["questions"][1]["options"]] == [2, 1]
    assert "isCorrect" not in response.text
    assert "correctOptionIDs" not in response.text
    assert client.get("/api/quizzes/3").status_code == 404


def test_submit_scores_multiple_choice_and_saves_attempt(env):
    client, engine = env
    response = submit(client)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["score"] == 100
    assert data["correctCount"] == 2
    assert data["totalCount"] == 2
    assert data["passed"] is True
    assert data["attemptNumber"] == 1
    assert [item["questionID"] for item in data["feedback"]] == [2, 1]
    assert "selectedOptionIDs" not in data["feedback"][0]
    with Session(engine) as db:
        result = db.scalar(select(QuizResult))
        assert result.score == 100
        assert result.attemptNumber == 1


def test_omitted_question_counts_as_wrong(env):
    client, _ = env
    response = submit(
        client,
        {"answers": [{"questionID": 1, "selectedOptionIDs": [2]}]},
    )
    data = response.json()["data"]
    assert data["score"] == 50
    assert data["correctCount"] == 1
    assert data["passed"] is False


def test_retry_and_filtered_history(env):
    client, _ = env
    assert client.get("/api/children/1/quiz-results?quizID=1").json()["data"] == []
    submit(client, {"answers": []})
    assert submit(client).json()["data"]["attemptNumber"] == 2
    rows = client.get("/api/children/1/quiz-results?quizID=1").json()["data"]
    assert [row["attemptNumber"] for row in rows] == [2, 1]
    assert [row["score"] for row in rows] == [100, 0]
    assert all(row["quizTitle"] == "বাংলা" for row in rows)
    assert all("feedback" not in row for row in rows)


@pytest.mark.parametrize(
    "body",
    [
        {
            "answers": [
                {"questionID": 1, "selectedOptionIDs": [2]},
                {"questionID": 1, "selectedOptionIDs": [2]},
            ]
        },
        {"answers": [{"questionID": 999, "selectedOptionIDs": [2]}]},
        {"answers": [{"questionID": 1, "selectedOptionIDs": [3]}]},
        {"answers": [{"questionID": 1, "selectedOptionIDs": [2, 2]}]},
        {"answers": [{"questionID": 1, "selectedOptionIDs": [2, 1]}]},
    ],
)
def test_invalid_answers_never_persist(env, body):
    client, engine = env
    response = submit(client, body)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "VALIDATION_FAILED"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(QuizResult)) == 0


def test_authentication_ownership_and_missing_records(env):
    client, _ = env
    assert submit(client, child=2).status_code == 403
    assert client.get("/api/children/2/quiz-results").status_code == 403
    assert submit(client, child=999).status_code == 404
    assert submit(client, quiz=999).status_code == 404
    assert submit(client, quiz=2).status_code == 404
    assert client.get("/api/children/1/quiz-results?quizID=999").status_code == 404
    client.cookies.clear()
    assert client.get("/api/quizzes?lessonID=1").status_code == 401
    assert client.get("/api/quizzes/1").status_code == 401
    assert submit(client).status_code == 401
    assert client.get("/api/children/1/quiz-results").status_code == 401


def test_commit_failure_rolls_back(env, monkeypatch):
    client, engine = env

    def fail_commit(self):
        raise RuntimeError("simulated storage failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    assert submit(client).status_code == 500
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(QuizResult)) == 0
