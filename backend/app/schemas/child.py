import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


PRESET_AVATARS = {"sprout", "bunny", "koala", "flower"}
CUSTOM_AVATAR_PATTERN = re.compile(
    r"^custom:[0-9]+-[a-f0-9]{32}\.(?:png|jpg|webp)$"
)


def _validate_avatar(value: str | None) -> str | None:
    if value is None:
        return value
    if value.startswith("custom:") and not CUSTOM_AVATAR_PATTERN.fullmatch(value):
        raise ValueError("Choose a valid avatar.")
    if value.strip():
        return value
    raise ValueError("Choose a valid avatar.")


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
    _validate_avatar_value = field_validator("avatar")(_validate_avatar)


class ChildUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=60)
    avatar: str | None = Field(default=None, max_length=150)
    ageBand: Literal["junior", "senior"] | None = None

    _validate_nickname = field_validator("nickname", mode="before")(
        _normalise_required_nickname
    )
    _validate_avatar_value = field_validator("avatar")(_validate_avatar)

    @field_validator("ageBand", mode="before")
    @classmethod
    def reject_null_age_band(cls, value):
        if value is None:
            raise ValueError("ageBand cannot be null")
        return value


class ChildDeleteConfirm(BaseModel):
    challenge_id: str
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("challenge_id")
    @classmethod
    def validate_challenge_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ValueError("The deletion verification request is invalid.") from exc


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
