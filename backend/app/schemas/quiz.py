from typing import List
from pydantic import BaseModel


class QuizOptionResponse(BaseModel):
    id: int
    text: str


class QuizQuestionResponse(BaseModel):
    id: int
    question_type: str
    question_text: str
    options: List[QuizOptionResponse] = []


class QuizResponse(BaseModel):
    id: int
    title: str
    level_id: int
    questions: List[QuizQuestionResponse]


class AnswerItem(BaseModel):
    question_id: int
    selected_option_ids: List[int]


class QuizSubmissionRequest(BaseModel):
    child_id: int
    answers: List[AnswerItem]


class AnswerResult(BaseModel):
    question_id: int
    correct: bool
    correct_option_ids: List[int]


class QuizSubmissionResponse(BaseModel):
    quiz_id: int
    child_id: int
    score: int
    total_questions: int
    percentage: float
    answers: List[AnswerResult]