from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_quizzes():
    return {
        "message": "Quiz API initialized"
    }


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int):
    return {
        "id": quiz_id,
        "title": "Sample Bangla Quiz",
        "level_id": 1,
        "questions": [
            {
                "id": 101,
                "question_type": "single_choice",
                "question_text": "Choose the correct Bangla letter",
                "options": [
                    {
                        "id": 1,
                        "text": "অ"
                    },
                    {
                        "id": 2,
                        "text": "আ"
                    },
                    {
                        "id": 3,
                        "text": "ই"
                    }
                ]
            }
        ]
    }


@router.post("/{quiz_id}/submit")
def submit_quiz(quiz_id: int):
    return {
        "quiz_id": quiz_id,
        "message": "Quiz submitted successfully"
    }


@router.get("/{quiz_id}/results")
def get_quiz_results(quiz_id: int):
    return {
        "quiz_id": quiz_id,
        "results": []
    }