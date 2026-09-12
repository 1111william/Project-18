from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, LearningLevel
from backend.app.schemas.child import ChildCreate, ChildOut, ChildSummary, ChildUpdate

router = APIRouter()


@router.get("")
def list_children(
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ChildProfile, LearningLevel.title)
        .join(LearningLevel, LearningLevel.levelID == ChildProfile.currentLevelID, isouter=True)
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


@router.post("")
def create_child(
    body: ChildCreate,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count()).select_from(ChildProfile).where(ChildProfile.parentID == parent_id)
    )
    if total >= settings.MAX_CHILDREN_PER_PARENT:
        raise ApiError(
            409,
            f"Maximum of {settings.MAX_CHILDREN_PER_PARENT} child profiles per account",
            ErrorCode.LIMIT_REACHED,
        )

    first_level = db.scalar(select(LearningLevel).order_by(LearningLevel.levelOrder).limit(1))

    child = ChildProfile(
        parentID=parent_id,
        nickname=body.nickname.strip(),
        avatar=body.avatar,
        ageBand=body.ageBand,
        currentLevelID=first_level.levelID if first_level else None,
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
    if body.nickname is not None:
        child.nickname = body.nickname.strip()
    if body.ageBand is not None:
        child.ageBand = body.ageBand
    if body.avatar is not None:
        child.avatar = body.avatar
    db.commit()

    return ok({"childID": child.childID})


@router.delete("/{childID}")
def delete_child(
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    child_id = child.childID
    db.delete(child)
    db.commit()

    return ok({"deleted": child_id})
