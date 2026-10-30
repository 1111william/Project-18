from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.responses import ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, Lesson, Quiz, QuizResult
from backend.app.schemas.quiz import QuizSubmissionRequest
from backend.app.services import quiz_service


router = APIRouter()
child_router = APIRouter()


@router.get("")
def get_quizzes(
    lessonID: Annotated[int, Query(gt=0)],
    db: Session = Depends(get_db),
    parent_id: int = Depends(current_parent_id),
):
    return ok(quiz_service.list_quizzes(db, lessonID))


@router.get("/{quizID}")
def get_quiz(
    quizID: int,
    db: Session = Depends(get_db),
    parent_id: int = Depends(current_parent_id),
):
    return ok(quiz_service.quiz_payload(quiz_service.load_quiz(db, quizID)))


@child_router.post("/{childID}/quizzes/{quizID}/attempts")
def submit_quiz(
    quizID: int,
    body: QuizSubmissionRequest,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    return ok(quiz_service.submit_quiz(db, quizID, child.childID, body))


@child_router.get("/{childID}/quiz-results")
def get_quiz_results(
    child: ChildProfile = Depends(owned_child),
    quizID: Annotated[int | None, Query(gt=0)] = None,
    db: Session = Depends(get_db),
):
    if quizID is not None:
        quiz_service.load_quiz(db, quizID)

    statement = (
        select(QuizResult, Quiz.title)
        .join(Quiz, Quiz.quizID == QuizResult.quizID)
        .join(Lesson, Lesson.lessonID == Quiz.lessonID)
        .where(
            QuizResult.childID == child.childID,
            Lesson.isPublished.is_(True),
        )
    )
    if quizID is not None:
        statement = statement.where(QuizResult.quizID == quizID)
    rows = db.execute(
        statement.order_by(QuizResult.submittedAt.desc(), QuizResult.resultID.desc())
    ).all()
    return ok(
        [quiz_service.result_payload(result, title) for result, title in rows]
    )
