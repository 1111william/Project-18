import base64
import json
import unittest
from unittest.mock import patch

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


class QuizApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
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
                    QuizOption(optionID=1, questionID=1, optionOrder=2, optionText="অ", isCorrect=False),
                    QuizOption(optionID=2, questionID=1, optionOrder=1, optionText="আ", isCorrect=True),
                    QuizOption(optionID=3, questionID=2, optionOrder=1, optionText="ক", isCorrect=True),
                    QuizOption(optionID=4, questionID=2, optionOrder=2, optionText="খ", isCorrect=True),
                    QuizOption(optionID=5, questionID=2, optionOrder=3, optionText="গ", isCorrect=False),
                ]
            )
            db.commit()

        def database():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = database
        self.client_context = TestClient(app, raise_server_exceptions=False)
        self.client = self.client_context.__enter__()
        payload = base64.b64encode(json.dumps({"parentID": 1}).encode())
        self.client.cookies.set(
            "session",
            TimestampSigner(settings.SESSION_SECRET).sign(payload).decode(),
        )
        self.client.headers["Origin"] = "http://testserver"

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.engine.dispose()

    @staticmethod
    def correct_answers():
        return {
            "answers": [
                {"questionID": 1, "selectedOptionIDs": [2]},
                {"questionID": 2, "selectedOptionIDs": [3, 4]},
            ]
        }

    def submit(self, body=None, child=1, quiz=1):
        return self.client.post(
            f"/api/children/{child}/quizzes/{quiz}/attempts",
            json=self.correct_answers() if body is None else body,
        )

    def test_list_quizzes_for_published_lesson(self):
        response = self.client.get("/api/quizzes?lessonID=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"],
            [
                {"quizID": 1, "lessonID": 1, "title": "বাংলা", "passMark": 70, "questionCount": 2},
                {"quizID": 2, "lessonID": 1, "title": "Empty", "passMark": 70, "questionCount": 0},
            ],
        )
        self.assertEqual(self.client.get("/api/quizzes?lessonID=2").status_code, 404)
        self.assertEqual(self.client.get("/api/quizzes?lessonID=999").status_code, 404)

    def test_quiz_detail_orders_content_without_leaking_answers(self):
        response = self.client.get("/api/quizzes/1")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["title"], "বাংলা")
        self.assertEqual([item["questionID"] for item in data["questions"]], [2, 1])
        self.assertEqual([item["optionID"] for item in data["questions"][1]["options"]], [2, 1])
        self.assertNotIn("isCorrect", response.text)
        self.assertNotIn("correctOptionIDs", response.text)
        self.assertEqual(self.client.get("/api/quizzes/3").status_code, 404)

    def test_submit_scores_multiple_choice_and_saves_attempt(self):
        response = self.submit()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["score"], 100)
        self.assertEqual(data["correctCount"], 2)
        self.assertEqual(data["totalCount"], 2)
        self.assertTrue(data["passed"])
        self.assertEqual(data["attemptNumber"], 1)
        self.assertEqual([item["questionID"] for item in data["feedback"]], [2, 1])
        self.assertNotIn("selectedOptionIDs", data["feedback"][0])
        with Session(self.engine) as db:
            result = db.scalar(select(QuizResult))
            self.assertEqual(result.score, 100)
            self.assertEqual(result.attemptNumber, 1)

    def test_omitted_question_counts_as_wrong(self):
        response = self.submit({"answers": [{"questionID": 1, "selectedOptionIDs": [2]}]})
        data = response.json()["data"]
        self.assertEqual(data["score"], 50)
        self.assertEqual(data["correctCount"], 1)
        self.assertFalse(data["passed"])

    def test_retry_and_filtered_history(self):
        self.assertEqual(self.client.get("/api/children/1/quiz-results?quizID=1").json()["data"], [])
        self.submit({"answers": []})
        self.assertEqual(self.submit().json()["data"]["attemptNumber"], 2)
        rows = self.client.get("/api/children/1/quiz-results?quizID=1").json()["data"]
        self.assertEqual([row["attemptNumber"] for row in rows], [2, 1])
        self.assertEqual([row["score"] for row in rows], [100, 0])
        self.assertTrue(all(row["quizTitle"] == "বাংলা" for row in rows))
        self.assertTrue(all("feedback" not in row for row in rows))

    def test_invalid_answers_never_persist(self):
        invalid_bodies = [
            {"answers": [{"questionID": 1, "selectedOptionIDs": [2]}, {"questionID": 1, "selectedOptionIDs": [2]}]},
            {"answers": [{"questionID": 999, "selectedOptionIDs": [2]}]},
            {"answers": [{"questionID": 1, "selectedOptionIDs": [3]}]},
            {"answers": [{"questionID": 1, "selectedOptionIDs": [2, 2]}]},
            {"answers": [{"questionID": 1, "selectedOptionIDs": [2, 1]}]},
        ]
        for body in invalid_bodies:
            with self.subTest(body=body):
                response = self.submit(body)
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(response.json()["code"], "VALIDATION_FAILED")
                with Session(self.engine) as db:
                    count = db.scalar(select(func.count()).select_from(QuizResult))
                    self.assertEqual(count, 0)

    def test_authentication_ownership_and_missing_records(self):
        self.assertEqual(self.submit(child=2).status_code, 403)
        self.assertEqual(self.client.get("/api/children/2/quiz-results").status_code, 403)
        self.assertEqual(self.submit(child=999).status_code, 404)
        self.assertEqual(self.submit(quiz=999).status_code, 404)
        self.assertEqual(self.submit(quiz=2).status_code, 404)
        self.assertEqual(self.client.get("/api/children/1/quiz-results?quizID=999").status_code, 404)
        self.client.cookies.clear()
        self.assertEqual(self.client.get("/api/quizzes?lessonID=1").status_code, 401)
        self.assertEqual(self.client.get("/api/quizzes/1").status_code, 401)
        self.assertEqual(self.submit().status_code, 401)
        self.assertEqual(self.client.get("/api/children/1/quiz-results").status_code, 401)

    def test_commit_failure_rolls_back(self):
        def fail_commit(_session):
            raise RuntimeError("simulated storage failure")

        with patch.object(Session, "commit", fail_commit):
            response = self.submit()
        self.assertEqual(response.status_code, 500)
        with Session(self.engine) as db:
            count = db.scalar(select(func.count()).select_from(QuizResult))
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
