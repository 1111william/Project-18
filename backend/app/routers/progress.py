from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ChildProfile, LearningLevel, Lesson, Progress

router = APIRouter()


@router.get("/")
def get_progress():
    return {
        "message": "Progress API initialized"
    }


@router.get("/{child_id}")
def get_child_progress(
    child_id: int,
    db: Session = Depends(get_db)
):
    # 1. Find the child
    child = db.scalar(
        select(ChildProfile)
        .where(ChildProfile.childID == child_id)
    )

    if child is None:
        return {
            "error": "Child not found"
        }

    # 2. Get the child's current learning level
    level = None

    if child.currentLevelID is not None:
        level = db.scalar(
            select(LearningLevel)
            .where(LearningLevel.levelID == child.currentLevelID)
        )

    # 3. Count lessons in the current level
    total_lessons = 0

    if child.currentLevelID is not None:
        total_lessons = db.scalar(
            select(func.count())
            .select_from(Lesson)
            .where(
                Lesson.levelID == child.currentLevelID,
                Lesson.isPublished == True
            )
        )

    # 4. Count completed lessons
    completed_lessons = 0

    if child.currentLevelID is not None:
        completed_lessons = db.scalar(
            select(func.count())
            .select_from(Progress)
            .join(Lesson, Progress.lessonID == Lesson.lessonID)
            .where(
                Progress.childID == child_id,
                Progress.completed == True,
                Lesson.levelID == child.currentLevelID
            )
        )

    # 5. Calculate overall progress percentage
    if total_lessons > 0:
        progress_percent = round(
            (completed_lessons / total_lessons) * 100
        )
    else:
        progress_percent = 0

    return {
        "child_id": child.childID,
        "nickname": child.nickname,
        "level_id": child.currentLevelID,
        "level_title": level.title if level else None,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "progress_percent": progress_percent
    }
@router.get("/{child_id}/level-status")
def get_level_status(child_id: int):
    # Mock data for prototype
    current_level = 1
    progress_percent = 100
    quiz_passed = True

    # Level-up rule:
    # 1. All lessons completed
    # 2. Quiz passed
    can_level_up = progress_percent == 100 and quiz_passed

    return {
        "child_id": child_id,
        "current_level": current_level,
        "progress_percent": progress_percent,
        "quiz_passed": quiz_passed,
        "can_level_up": can_level_up
    }
from pydantic import BaseModel


class ProgressUpdate(BaseModel):
    percent_complete: int
    seconds_spent: int = 0


# Temporary in-memory storage for prototype
mock_progress_store = {}


@router.put("/{child_id}/lessons/{lesson_id}")
def update_lesson_progress(
    child_id: int,
    lesson_id: int,
    data: ProgressUpdate
):
    # Keep progress between 0 and 100
    percent_complete = max(0, min(data.percent_complete, 100))

    mock_progress_store[(child_id, lesson_id)] = {
        "child_id": child_id,
        "lesson_id": lesson_id,
        "percent_complete": percent_complete,
        "seconds_spent": data.seconds_spent,
        "completed": percent_complete == 100
    }

    return mock_progress_store[(child_id, lesson_id)]
@router.get("/{child_id}/lessons/{lesson_id}")
def get_lesson_progress(
    child_id: int,
    lesson_id: int
):
    progress = mock_progress_store.get((child_id, lesson_id))

    if progress is None:
        return {
            "child_id": child_id,
            "lesson_id": lesson_id,
            "message": "No progress record found"
        }

    return progress
LEVELS = {
    1: {
        "name": "Beginner",
        "description": "Basic Bangla learning level",
        "pass_requirement": 70
    },
    2: {
        "name": "Intermediate",
        "description": "Intermediate Bangla learning level",
        "pass_requirement": 75
    },
    3: {
        "name": "Advanced",
        "description": "Advanced Bangla learning level",
        "pass_requirement": 80
    }
}


@router.get("/levels/{level}")
def get_learning_level(level: int):
    level_info = LEVELS.get(level)

    if level_info is None:
        return {
            "error": "Learning level not found"
        }

    return {
        "level": level,
        "name": level_info["name"],
        "description": level_info["description"],
        "pass_requirement": level_info["pass_requirement"]
    }