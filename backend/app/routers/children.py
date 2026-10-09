import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, Parent
from backend.app.schemas.child import ChildCreate, ChildDeleteConfirm, ChildOut, ChildSummary, ChildUpdate
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
AVATAR_FILENAME_PATTERN = re.compile(r"^[0-9]+-[a-f0-9]{32}\.(?:png|jpg|webp)$")


def avatar_bytes_match_type(data: bytes, extension: str) -> bool:
    if extension == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == "jpg":
        return data.startswith(b"\xff\xd8\xff")
    return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def custom_avatar_filename(avatar: str) -> str | None:
    if not avatar.startswith("custom:"):
        return None
    filename = avatar.removeprefix("custom:")
    return filename if AVATAR_FILENAME_PATTERN.fullmatch(filename) else None


def remove_custom_avatar(avatar: str) -> None:
    filename = custom_avatar_filename(avatar)
    if filename:
        (AVATAR_DIRECTORY / filename).unlink(missing_ok=True)


def require_owned_avatar(avatar: str, parent_id: int) -> None:
    filename = custom_avatar_filename(avatar)
    if filename and not filename.startswith(f"{parent_id}-"):
        raise ApiError(400, "Choose a valid avatar.", ErrorCode.VALIDATION_FAILED, ["avatar"])


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
        raise ApiError(400, "Choose an image smaller than 2 MB.", ErrorCode.VALIDATION_FAILED, ["avatar"])
    if not avatar_bytes_match_type(data, extension):
        raise ApiError(400, "The selected file is not a valid image.", ErrorCode.VALIDATION_FAILED, ["avatar"])

    AVATAR_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = f"{parent_id}-{uuid.uuid4().hex}.{extension}"
    (AVATAR_DIRECTORY / filename).write_bytes(data)
    return ok({"avatar": f"custom:{filename}", "url": f"/api/children/avatars/{filename}"})


@router.get("/avatars/{filename}")
def get_avatar(filename: str):
    if not AVATAR_FILENAME_PATTERN.fullmatch(filename):
        raise ApiError(404, "Avatar not found", ErrorCode.NOT_FOUND)
    path = AVATAR_DIRECTORY / filename
    if not path.is_file():
        raise ApiError(404, "Avatar not found", ErrorCode.NOT_FOUND)
    media_type = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}[path.suffix[1:]]
    return FileResponse(path, media_type=media_type)


@router.get("")
def list_children(
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    children = db.scalars(
        select(ChildProfile)
        .where(ChildProfile.parentID == parent_id)
        .order_by(ChildProfile.createdAt)
    ).all()

    return ok([ChildSummary.model_validate(child) for child in children])


@router.get("/{childID}")
def get_child(child: ChildProfile = Depends(owned_child)):
    return ok(ChildOut.model_validate(child))


@router.post("")
def create_child(
    body: ChildCreate,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    require_owned_avatar(body.avatar, parent_id)
    total = db.scalar(
        select(func.count()).select_from(ChildProfile).where(ChildProfile.parentID == parent_id)
    )
    if total >= settings.MAX_CHILDREN_PER_PARENT:
        raise ApiError(
            409,
            f"Maximum of {settings.MAX_CHILDREN_PER_PARENT} child profiles per account",
            ErrorCode.LIMIT_REACHED,
        )

    child = ChildProfile(
        parentID=parent_id,
        nickname=body.nickname.strip(),
        age=body.age,
        avatar=body.avatar,
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    return ok({"childID": child.childID})


@router.put("/{childID}")
def update_child(
    body: ChildUpdate,
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    previous_avatar = child.avatar
    if body.nickname is not None:
        child.nickname = body.nickname.strip()
    if body.age is not None:
        child.age = body.age
    if body.avatar is not None:
        require_owned_avatar(body.avatar, child.parentID)
        child.avatar = body.avatar
    db.commit()
    if body.avatar is not None and body.avatar != previous_avatar:
        remove_custom_avatar(previous_avatar)

    return ok({"childID": child.childID})


@router.post("/{childID}/delete-code")
def request_child_delete_code(
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    parent = db.get(Parent, child.parentID)
    if parent is None:
        raise ApiError(401, "Sign in required", ErrorCode.UNAUTHENTICATED)

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
    db.delete(child)
    db.commit()
    remove_custom_avatar(avatar)
    registration_challenges.consume(challenge.challenge_id)

    return ok({"deleted": child_id})
