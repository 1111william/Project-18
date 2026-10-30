import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, Unauthenticated, ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, LearningLevel, Lesson, Parent, Progress
from backend.app.schemas.child import (
    ChildCreate,
    ChildDeleteConfirm,
    ChildOut,
    ChildSummary,
    ChildUpdate,
)
from backend.app.services.account_auth import registration_challenges
from backend.app.services.email_service import send_verification_code


router = APIRouter()

AVATAR_DIRECTORY = Path(__file__).resolve().parents[2] / ".local" / "avatars"
MAX_AVATAR_BYTES = 2 * 1024 * 1024
AVATAR_CONTENT_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}
AVATAR_FILENAME_PATTERN = re.compile(
    r"^[0-9]+-[a-f0-9]{32}\.(?:png|jpg|webp)$"
)


def _avatar_bytes_match_type(data: bytes, extension: str) -> bool:
    if extension == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == "jpg":
        return data.startswith(b"\xff\xd8\xff")
    return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def _custom_avatar_filename(avatar: str | None) -> str | None:
    if not avatar or not avatar.startswith("custom:"):
        return None
    filename = avatar.removeprefix("custom:")
    return filename if AVATAR_FILENAME_PATTERN.fullmatch(filename) else None


def remove_custom_avatar(avatar: str | None) -> None:
    filename = _custom_avatar_filename(avatar)
    if filename:
        (AVATAR_DIRECTORY / filename).unlink(missing_ok=True)


def _require_owned_avatar(avatar: str | None, parent_id: int) -> None:
    filename = _custom_avatar_filename(avatar)
    if filename and not filename.startswith(f"{parent_id}-"):
        raise ApiError(
            400,
            "Choose a valid avatar.",
            ErrorCode.VALIDATION_FAILED,
            ["avatar"],
        )


def save_custom_avatar(data: bytes, extension: str, parent_id: int) -> str:
    """Persist a validated avatar payload and return its stored avatar value."""
    if extension not in AVATAR_CONTENT_TYPES.values() or not _avatar_bytes_match_type(
        data, extension
    ):
        raise ApiError(
            400,
            "The selected file is not a valid image.",
            ErrorCode.VALIDATION_FAILED,
            ["avatar"],
        )
    AVATAR_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = f"{parent_id}-{uuid.uuid4().hex}.{extension}"
    (AVATAR_DIRECTORY / filename).write_bytes(data)
    return f"custom:{filename}"


@router.post("/avatar")
async def upload_avatar(
    request: Request,
    parent_id: int = Depends(current_parent_id),
):
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    extension = AVATAR_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ApiError(
            400,
            "Choose a PNG, JPG, or WebP image.",
            ErrorCode.VALIDATION_FAILED,
            ["avatar"],
        )

    content_length = request.headers.get("content-length")
    try:
        content_too_large = bool(content_length) and int(content_length) > MAX_AVATAR_BYTES
    except ValueError:
        content_too_large = True
    if content_too_large:
        raise ApiError(
            400,
            "Choose an image smaller than 2 MB.",
            ErrorCode.VALIDATION_FAILED,
            ["avatar"],
        )

    data = await request.body()
    if not data or len(data) > MAX_AVATAR_BYTES:
        raise ApiError(
            400,
            "Choose an image smaller than 2 MB.",
            ErrorCode.VALIDATION_FAILED,
            ["avatar"],
        )
    avatar = save_custom_avatar(data, extension, parent_id)
    filename = avatar.removeprefix("custom:")
    return ok(
        {
            "avatar": avatar,
            "url": f"/api/children/avatars/{filename}",
        }
    )


@router.get("/avatars/{filename}")
def get_avatar(filename: str):
    if not AVATAR_FILENAME_PATTERN.fullmatch(filename):
        raise ApiError(404, "Avatar not found", ErrorCode.NOT_FOUND)
    path = AVATAR_DIRECTORY / filename
    if not path.is_file():
        raise ApiError(404, "Avatar not found", ErrorCode.NOT_FOUND)
    media_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "webp": "image/webp",
    }[path.suffix[1:]]
    return FileResponse(path, media_type=media_type)


@router.get("")
def list_children(
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ChildProfile, LearningLevel.title)
        .join(
            LearningLevel,
            LearningLevel.levelID == ChildProfile.currentLevelID,
            isouter=True,
        )
        .where(ChildProfile.parentID == parent_id)
        .order_by(ChildProfile.createdAt)
    ).all()

    payload = []
    for child, level_title in rows:
        summary = ChildSummary.model_validate(child)
        summary.levelTitle = level_title
        payload.append(summary)

    return ok(payload)


@router.get("/{childID}")
def get_child(child: ChildProfile = Depends(owned_child)):
    return ok(ChildOut.model_validate(child))


@router.get("/{childID}/home")
def get_student_home(
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    level = db.get(LearningLevel, child.currentLevelID) if child.currentLevelID else None
    rows = []
    if child.currentLevelID:
        rows = db.execute(
            select(Lesson, Progress)
            .outerjoin(
                Progress,
                and_(
                    Progress.lessonID == Lesson.lessonID,
                    Progress.childID == child.childID,
                ),
            )
            .where(
                Lesson.levelID == child.currentLevelID,
                Lesson.isPublished.is_(True),
            )
            .order_by(Lesson.strand, Lesson.lessonOrder)
        ).all()

    lessons = [
        {
            "lessonID": lesson.lessonID,
            "strand": lesson.strand,
            "title": lesson.title,
            "summary": lesson.summary,
            "estimatedMinutes": lesson.estimatedMinutes,
            "percentComplete": progress.percentComplete if progress else 0,
            "completed": progress.completed if progress else False,
        }
        for lesson, progress in rows
    ]
    completed_lessons = sum(1 for lesson in lessons if lesson["completed"])
    overall_progress = (
        round(sum(lesson["percentComplete"] for lesson in lessons) / len(lessons))
        if lessons
        else 0
    )

    return ok(
        {
            "child": {
                "childID": child.childID,
                "nickname": child.nickname,
                "avatar": child.avatar,
                "ageBand": child.ageBand,
                "currentLevelID": child.currentLevelID,
                "levelTitle": level.title if level else None,
            },
            "level": (
                {
                    "title": level.title,
                    "description": level.description,
                }
                if level
                else None
            ),
            "summary": {
                "lessonCount": len(lessons),
                "completedLessons": completed_lessons,
                "overallProgress": overall_progress,
            },
            "lessons": lessons,
        }
    )


@router.post("")
def create_child(
    body: ChildCreate,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    _require_owned_avatar(body.avatar, parent_id)
    try:
        # Serialize creation per parent so concurrent requests cannot both
        # observe the same pre-limit count on MySQL/InnoDB.
        parent = db.scalar(
            select(Parent)
            .where(Parent.parentID == parent_id)
            .with_for_update()
        )
        if parent is None:
            raise Unauthenticated("Session account no longer exists")

        child_ids = db.scalars(
            select(ChildProfile.childID)
            .where(ChildProfile.parentID == parent_id)
            .with_for_update()
        ).all()
        if len(child_ids) >= settings.MAX_CHILDREN_PER_PARENT:
            raise ApiError(
                409,
                f"Maximum of {settings.MAX_CHILDREN_PER_PARENT} child profiles per account",
                ErrorCode.LIMIT_REACHED,
            )

        first_level = db.scalar(
            select(LearningLevel).order_by(LearningLevel.levelOrder).limit(1)
        )
        child = ChildProfile(
            parentID=parent_id,
            nickname=body.nickname,
            avatar=body.avatar,
            ageBand=body.ageBand,
            currentLevelID=first_level.levelID if first_level else None,
        )
        db.add(child)
        db.flush()
        child_id = child.childID
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ok({"childID": child_id})


@router.put("/{childID}")
def update_child(
    body: ChildUpdate,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    previous_avatar = child.avatar
    if "avatar" in body.model_fields_set:
        _require_owned_avatar(body.avatar, child.parentID)
    try:
        fields_set = body.model_fields_set
        if "nickname" in fields_set:
            child.nickname = body.nickname
        if "ageBand" in fields_set:
            child.ageBand = body.ageBand
        if "avatar" in fields_set:
            child.avatar = body.avatar

        child_id = child.childID
        db.commit()
    except Exception:
        db.rollback()
        raise
    if "avatar" in body.model_fields_set and body.avatar != previous_avatar:
        remove_custom_avatar(previous_avatar)
    return ok({"childID": child_id})


@router.post("/{childID}/delete-code")
def request_child_delete_code(
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    parent = db.get(Parent, child.parentID)
    if parent is None:
        raise Unauthenticated("Session account no longer exists")

    challenge, code = registration_challenges.create_child_delete(
        parent.email,
        parent.parentID,
        child.childID,
    )
    delivery = send_verification_code(challenge.email, code, challenge.purpose)
    data = {
        "challenge_id": challenge.challenge_id,
        "purpose": challenge.purpose,
        "expires_at": challenge.expires_at,
        "resend_at": challenge.resend_at,
        "delivery": delivery,
    }
    if settings.AUTH_DEVELOPMENT_CODES:
        data["development_code"] = code
    return ok(data)


@router.delete("/{childID}")
def delete_child(
    body: ChildDeleteConfirm,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    challenge = registration_challenges.verify(body.challenge_id, body.code)
    if (
        challenge.purpose != "child_delete"
        or challenge.parent_id != child.parentID
        or challenge.child_id != child.childID
    ):
        raise ApiError(
            400,
            "The deletion verification request is invalid.",
            ErrorCode.VALIDATION_FAILED,
            ["code"],
        )

    child_id = child.childID
    avatar = child.avatar
    try:
        db.delete(child)
        db.commit()
    except Exception:
        db.rollback()
        raise

    remove_custom_avatar(avatar)
    registration_challenges.consume(challenge.challenge_id)
    return ok({"deleted": child_id})
