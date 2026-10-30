from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.responses import ApiError, ErrorCode, NotFound
from backend.app.models import ChildProfile, Lesson, Quiz, QuizQuestion, QuizResult
from backend.app.schemas.quiz import QuizSubmissionRequest


def invalid(message: str, field: str = "answers") -> None:
    raise ApiError(400, message, ErrorCode.VALIDATION_FAILED, [field])


def load_published_lesson(db: Session, lesson_id: int) -> Lesson:
    lesson = db.scalar(
        select(Lesson).where(
            Lesson.lessonID == lesson_id,
            Lesson.isPublished.is_(True),
        )
    )
    if lesson is None:
        raise NotFound("Lesson not found")
    return lesson


def load_quiz(db: Session, quiz_id: int) -> Quiz:
    quiz = db.scalar(
        select(Quiz)
        .join(Lesson, Lesson.lessonID == Quiz.lessonID)
        .where(
            Quiz.quizID == quiz_id,
            Lesson.isPublished.is_(True),
        )
        .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
    )
    if quiz is None:
        raise NotFound("Quiz not found")
    return quiz


def ordered_questions(quiz: Quiz) -> list[QuizQuestion]:
    return sorted(
        quiz.questions,
        key=lambda question: (question.questionOrder, question.questionID),
    )


def list_quizzes(db: Session, lesson_id: int) -> list[dict]:
    load_published_lesson(db, lesson_id)
    rows = db.execute(
        select(Quiz, func.count(QuizQuestion.questionID))
        .outerjoin(QuizQuestion, QuizQuestion.quizID == Quiz.quizID)
        .where(Quiz.lessonID == lesson_id)
        .group_by(Quiz.quizID)
        .order_by(Quiz.quizID)
    ).all()
    return [
        {
            "quizID": quiz.quizID,
            "lessonID": quiz.lessonID,
            "title": quiz.title,
            "passMark": quiz.passMark,
            "questionCount": question_count,
        }
        for quiz, question_count in rows
    ]


def quiz_payload(quiz: Quiz) -> dict:
    return {
        "quizID": quiz.quizID,
        "lessonID": quiz.lessonID,
        "title": quiz.title,
        "passMark": quiz.passMark,
        "questions": [
            {
                "questionID": question.questionID,
                "questionOrder": question.questionOrder,
                "questionKind": question.questionKind,
                "prompt": question.prompt,
                "mediaPath": question.mediaPath,
                "options": [
                    {
                        "optionID": option.optionID,
                        "optionOrder": option.optionOrder,
                        "optionText": option.optionText,
                    }
                    for option in sorted(
                        question.options,
                        key=lambda item: (item.optionOrder, item.optionID),
                    )
                ],
            }
            for question in ordered_questions(quiz)
        ],
    }


def calculate_score(
    submitted_answers: dict[int, set[int]],
    quiz: Quiz,
) -> tuple[int, list[dict]]:
    feedback = []
    for question in ordered_questions(quiz):
        correct_option_ids = {
            option.optionID for option in question.options if option.isCorrect
        }
        selected_option_ids = submitted_answers.get(question.questionID, set())
        feedback.append(
            {
                "questionID": question.questionID,
                "correct": selected_option_ids == correct_option_ids,
                "correctOptionIDs": sorted(correct_option_ids),
            }
        )
    return sum(item["correct"] for item in feedback), feedback


def validate_answers(
    body: QuizSubmissionRequest,
    quiz: Quiz,
) -> dict[int, set[int]]:
    questions = {question.questionID: question for question in ordered_questions(quiz)}
    submitted: dict[int, set[int]] = {}

    for index, answer in enumerate(body.answers):
        question_field = f"answers[{index}].questionID"
        option_field = f"answers[{index}].selectedOptionIDs"
        question = questions.get(answer.questionID)
        if question is None:
            invalid("Question does not belong to this quiz", question_field)
        if answer.questionID in submitted:
            invalid("Question appears more than once", question_field)

        selected = set(answer.selectedOptionIDs)
        if len(selected) != len(answer.selectedOptionIDs):
            invalid("An option cannot be selected more than once", option_field)

        available = {option.optionID for option in question.options}
        if not selected.issubset(available):
            invalid("Selected option does not belong to its question", option_field)

        correct = {option.optionID for option in question.options if option.isCorrect}
        if question.questionKind in {"single", "boolean"}:
            if len(selected) != 1 or len(correct) != 1:
                invalid("This question requires exactly one answer", option_field)
            if question.questionKind == "boolean" and len(available) != 2:
                invalid("Boolean questions must contain two options", option_field)
        elif question.questionKind == "multiple":
            if not correct:
                invalid("Multiple-choice question has no correct answer", question_field)
        else:
            invalid("Quiz question type is not supported", question_field)

        submitted[answer.questionID] = selected

    return submitted


def submission_payload(result: QuizResult, feedback: list[dict]) -> dict:
    return {
        "resultID": result.resultID,
        "quizID": result.quizID,
        "score": result.score,
        "correctCount": result.correctCount,
        "totalCount": result.totalCount,
        "passed": result.passed,
        "attemptNumber": result.attemptNumber,
        "submittedAt": result.submittedAt,
        "feedback": feedback,
    }


def result_payload(result: QuizResult, quiz_title: str) -> dict:
    return {
        "resultID": result.resultID,
        "quizID": result.quizID,
        "quizTitle": quiz_title,
        "score": result.score,
        "correctCount": result.correctCount,
        "totalCount": result.totalCount,
        "passed": result.passed,
        "attemptNumber": result.attemptNumber,
        "submittedAt": result.submittedAt,
    }


def submit_quiz(
    db: Session,
    quiz_id: int,
    child_id: int,
    body: QuizSubmissionRequest,
) -> dict:
    try:
        child = db.scalar(
            select(ChildProfile)
            .where(ChildProfile.childID == child_id)
            .with_for_update()
        )
        if child is None:
            raise NotFound("Child profile not found")

        quiz = load_quiz(db, quiz_id)
        questions = ordered_questions(quiz)
        if not questions:
            raise NotFound("Quiz has no questions")

        submitted = validate_answers(body, quiz)
        correct_count, feedback = calculate_score(submitted, quiz)
        total_count = len(questions)
        score = round(correct_count * 100 / total_count)

        last_attempt = db.scalar(
            select(QuizResult.attemptNumber)
            .where(
                QuizResult.childID == child_id,
                QuizResult.quizID == quiz_id,
            )
            .order_by(QuizResult.attemptNumber.desc())
            .limit(1)
            .with_for_update()
        )
        result = QuizResult(
            childID=child_id,
            quizID=quiz_id,
            score=score,
            correctCount=correct_count,
            totalCount=total_count,
            passed=score >= quiz.passMark,
            attemptNumber=(last_attempt or 0) + 1,
        )
        db.add(result)
        db.flush()
        db.refresh(result)
        response = submission_payload(result, feedback)
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise
