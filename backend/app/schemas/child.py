from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChildCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    avatar: Optional[str] = Field(default=None, max_length=150)
    ageBand: Literal["junior", "senior"] = "junior"


class ChildUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=60)
    avatar: Optional[str] = Field(default=None, max_length=150)
    ageBand: Optional[Literal["junior", "senior"]] = None


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    childID: int
    parentID: int
    nickname: str
    avatar: Optional[str]
    ageBand: str
    currentLevelID: Optional[int]
    createdAt: Optional[datetime]


class ChildSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    childID: int
    nickname: str
    avatar: Optional[str]
    ageBand: str
    currentLevelID: Optional[int]
    levelTitle: Optional[str] = None
