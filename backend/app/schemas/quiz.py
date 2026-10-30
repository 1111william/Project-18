from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


PositiveID = Annotated[int, Field(strict=True, gt=0)]


class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questionID: PositiveID
    selectedOptionIDs: list[PositiveID] = Field(min_length=1)


class QuizSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[AnswerItem] = Field(default_factory=list)
