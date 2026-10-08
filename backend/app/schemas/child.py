from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalise_required_nickname(value):
    if value is None:
        raise ValueError("nickname cannot be null")
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        raise ValueError("nickname must not be blank")
    return value


class ChildCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    avatar: str | None = Field(default=None, max_length=150)
    ageBand: Literal["junior", "senior"] = "junior"

    _validate_nickname = field_validator("nickname", mode="before")(
        _normalise_required_nickname
    )


class ChildUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=60)
    avatar: str | None = Field(default=None, max_length=150)
    ageBand: Literal["junior", "senior"] | None = None

    _validate_nickname = field_validator("nickname", mode="before")(
        _normalise_required_nickname
    )

    @field_validator("ageBand", mode="before")
    @classmethod
    def reject_null_age_band(cls, value):
        if value is None:
            raise ValueError("ageBand cannot be null")
        return value


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    childID: int
    parentID: int
    nickname: str
    avatar: str | None
    ageBand: str
    currentLevelID: int | None
    createdAt: datetime | None


class ChildSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    childID: int
    nickname: str
    avatar: str | None
    ageBand: str
    currentLevelID: int | None
    levelTitle: str | None = None
