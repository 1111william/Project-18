import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


PRESET_AVATARS = {"sprout", "bunny", "koala", "flower"}
CUSTOM_AVATAR_PATTERN = re.compile(r"^custom:[0-9]+-[a-f0-9]{32}\.(?:png|jpg|webp)$")


def validate_avatar_value(value: str) -> str:
    if value in PRESET_AVATARS or CUSTOM_AVATAR_PATTERN.fullmatch(value):
        return value
    raise ValueError("Choose a valid avatar.")


def validate_optional_avatar_value(value: Optional[str]) -> Optional[str]:
    return None if value is None else validate_avatar_value(value)


class ChildCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    age: int = Field(gt=0)
    avatar: str = Field(default="sprout", max_length=150)

    _validate_avatar = field_validator("avatar")(validate_avatar_value)


class ChildUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=60)
    age: Optional[int] = Field(default=None, gt=0)
    avatar: Optional[str] = Field(default=None, max_length=150)

    _validate_avatar = field_validator("avatar")(validate_optional_avatar_value)


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
    age: int
    avatar: str
    createdAt: Optional[datetime]


class ChildSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    childID: int
    nickname: str
    age: int
    avatar: str
