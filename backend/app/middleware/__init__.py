import logging

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import ErrorCode, Forbidden, NotFound, Unauthenticated
from backend.app.database import get_db
from backend.app.models import ChildProfile

logger = logging.getLogger("api")


def current_parent_id(request: Request) -> int:
    parent_id = request.session.get("parentID")
    if parent_id is None:
        raise Unauthenticated()
    return int(parent_id)


def require_admin(request: Request) -> int:
    parent_id = current_parent_id(request)
    if not request.session.get("isAdmin"):
        raise Forbidden("Administrator access required")
    return parent_id


def require_pin(request: Request) -> None:
    current_parent_id(request)
    if not request.session.get("pinVerified"):
        raise Forbidden("PIN verification required", ErrorCode.PIN_REQUIRED)


def owned_child(
    childID: int,
    request: Request,
    db: Session = Depends(get_db),
) -> ChildProfile:
    parent_id = current_parent_id(request)
    child = db.get(ChildProfile, childID)

    if child is None:
        raise NotFound("Child profile not found")

    if child.parentID != parent_id and not request.session.get("isAdmin"):
        logger.warning("Ownership violation: parent %s requested child %s", parent_id, childID)
        raise Forbidden("This child profile does not belong to your account")

    return child
