from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, Unauthenticated, ok
from backend.app.database import get_db
from backend.app.middleware import current_parent_id, owned_child
from backend.app.models import ChildProfile, LearningLevel, Parent
from backend.app.schemas.child import ChildCreate, ChildOut, ChildSummary, ChildUpdate


router = APIRouter()


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


@router.post("")
def create_child(
    body: ChildCreate,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
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
    return ok({"childID": child_id})


@router.delete("/{childID}")
def delete_child(
    child: ChildProfile = Depends(owned_child),
    db: Session = Depends(get_db),
):
    child_id = child.childID
    try:
        db.delete(child)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ok({"deleted": child_id})
