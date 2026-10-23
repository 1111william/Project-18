from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.responses import ApiError, ErrorCode, ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, LearningLevel, Lesson, Progress


router = APIRouter()
progress_router = APIRouter()


# =========================================================
# Request body
# =========================================================

class ProgressUpdate(BaseModel):
    percentComplete: int
    secondsSpent: int
    completed: bool = False


# =========================================================
# GET /api/levels
# =========================================================

@router.get("/levels")
def get_levels(
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    levels = db.scalars(
        select(LearningLevel)
        .order_by(
            LearningLevel.levelOrder,
            LearningLevel.levelID,
        )
    ).all()

    data = []

    for level in levels:
        lessons = db.scalars(
            select(Lesson)
            .where(
                Lesson.levelID == level.levelID,
                Lesson.isPublished.is_(True),
            )
        ).all()

        data.append(
            {
                "levelID": level.levelID,
                "levelOrder": level.levelOrder,
                "title": level.title,
                "description": level.description,
                "passMark": level.passMark,
                "lessonCount": len(lessons),
            }
        )

    return ok(data)


# =========================================================
# GET /api/levels/{levelID}/lessons
# =========================================================

@router.get("/levels/{levelID}/lessons")
def get_level_lessons(
    levelID: int,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    level = db.scalar(
        select(LearningLevel)
        .where(
            LearningLevel.levelID == levelID
        )
    )

    if level is None:
        raise ApiError(
            404,
            "Learning level not found",
            ErrorCode.NOT_FOUND,
        )

    lessons = db.scalars(
        select(Lesson)
        .where(
            Lesson.levelID == levelID,
            Lesson.isPublished.is_(True),
        )
        .order_by(
            Lesson.lessonOrder,
            Lesson.lessonID,
        )
    ).all()

    data = [
        {
            "lessonID": lesson.lessonID,
            "levelID": lesson.levelID,
            "strand": lesson.strand,
            "lessonOrder": lesson.lessonOrder,
            "title": lesson.title,
            "summary": lesson.summary,
            "coverImage": lesson.coverImage,
            "estimatedMinutes": lesson.estimatedMinutes,
        }
        for lesson in lessons
    ]

    return ok(data)


# =========================================================
# GET /api/children/{childID}/progress
# =========================================================

@progress_router.get("/{childID}/progress")
def get_child_progress(
    childID: int,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    # Child has no current level yet
    if child.currentLevelID is None:
        return ok(
            {
                "currentLevelID": None,
                "completedLessons": 0,
                "totalLessons": 0,
                "overallPercent": 0,
                "lessons": [],
            }
        )

    lessons = db.scalars(
        select(Lesson)
        .where(
            Lesson.levelID == child.currentLevelID,
            Lesson.isPublished.is_(True),
        )
        .order_by(
            Lesson.lessonOrder,
            Lesson.lessonID,
        )
    ).all()

    progress_rows = db.scalars(
        select(Progress)
        .where(
            Progress.childID == child.childID
        )
    ).all()

    progress_by_lesson = {
        row.lessonID: row
        for row in progress_rows
    }

    lesson_data = []
    total_percent = 0
    completed_count = 0

    for lesson in lessons:
        progress = progress_by_lesson.get(
            lesson.lessonID
        )

        if progress is None:
            percent_complete = 0
            completed = False
            seconds_spent = 0
            last_viewed_at = None
        else:
            percent_complete = progress.percentComplete
            completed = progress.completed
            seconds_spent = progress.secondsSpent
            last_viewed_at = progress.lastViewedAt

        total_percent += percent_complete

        if completed:
            completed_count += 1

        lesson_data.append(
            {
                "lessonID": lesson.lessonID,
                "percentComplete": percent_complete,
                "completed": completed,
                "secondsSpent": seconds_spent,
                "lastViewedAt": last_viewed_at,
            }
        )

    total_lessons = len(lessons)

    overall_percent = (
        round(total_percent / total_lessons)
        if total_lessons > 0
        else 0
    )

    return ok(
        {
            "currentLevelID": child.currentLevelID,
            "completedLessons": completed_count,
            "totalLessons": total_lessons,
            "overallPercent": overall_percent,
            "lessons": lesson_data,
        }
    )


# =========================================================
# POST /api/children/{childID}/lessons/{lessonID}/progress
# =========================================================

@progress_router.post(
    "/{childID}/lessons/{lessonID}/progress"
)
def update_lesson_progress(
    childID: int,
    lessonID: int,
    body: ProgressUpdate,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    # Validate request values
    if body.percentComplete < 0 or body.percentComplete > 100:
        raise ApiError(
            400,
            "percentComplete must be between 0 and 100",
            ErrorCode.VALIDATION_FAILED,
        )

    if body.secondsSpent < 0 or body.secondsSpent > 3600:
        raise ApiError(
            400,
            "secondsSpent must be between 0 and 3600",
            ErrorCode.VALIDATION_FAILED,
        )

    # Only published lessons are visible
    lesson = db.scalar(
        select(Lesson)
        .where(
            Lesson.lessonID == lessonID,
            Lesson.isPublished.is_(True),
        )
    )

    if lesson is None:
        raise ApiError(
            404,
            "Lesson not found",
            ErrorCode.NOT_FOUND,
        )

    # Lock an existing row so concurrent updates
    # do not overwrite each other's time values.
    progress = db.scalar(
        select(Progress)
        .where(
            Progress.childID == child.childID,
            Progress.lessonID == lessonID,
        )
        .with_for_update()
    )

    if progress is None:
        percent_complete = body.percentComplete

        if body.completed:
            percent_complete = 100

        progress = Progress(
            childID=child.childID,
            lessonID=lessonID,
            percentComplete=percent_complete,
            completed=body.completed,
            secondsSpent=body.secondsSpent,
        )

        db.add(progress)

        try:
            db.commit()

        except IntegrityError:
            # Another request may have created the row
            # at the same moment.
            db.rollback()

            progress = db.scalar(
                select(Progress)
                .where(
                    Progress.childID
                    == child.childID,
                    Progress.lessonID
                    == lessonID,
                )
                .with_for_update()
            )

            if progress is None:
                raise

            progress.percentComplete = max(
                progress.percentComplete,
                body.percentComplete,
            )

            progress.secondsSpent += (
                body.secondsSpent
            )

            progress.completed = (
                progress.completed
                or body.completed
            )

            if progress.completed:
                progress.percentComplete = 100

            from sqlalchemy import func

            progress.lastViewedAt = func.now()

            db.commit()

    else:
        progress.percentComplete = max(
            progress.percentComplete,
            body.percentComplete,
        )

        progress.secondsSpent += (
            body.secondsSpent
        )

        progress.completed = (
            progress.completed
            or body.completed
        )

        if progress.completed:
            progress.percentComplete = 100

        from sqlalchemy import func

        progress.lastViewedAt = func.now()

        db.commit()

    db.refresh(progress)

    return ok(
        {
            "lessonID": progress.lessonID,
            "percentComplete": progress.percentComplete,
            "completed": progress.completed,
            "secondsSpent": progress.secondsSpent,
            "lastViewedAt": progress.lastViewedAt,
        }
    )