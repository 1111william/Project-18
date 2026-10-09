import logging

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import ErrorCode, Forbidden, NotFound, Unauthenticated
from backend.app.database import get_db
from backend.app.models import ChildProfile, Parent


logger = logging.getLogger("api")


def _clear_invalid_session(request: Request) -> None:
    try:
        request.session.clear()
    except (AssertionError, AttributeError):
        # A missing SessionMiddleware is a framework setup error, but guards
        # still return a safe 401 instead of leaking a conversion exception.
        pass


def _authenticated_parent(request: Request, db: Session) -> Parent:
    try:
        session = request.session
    except (AssertionError, AttributeError):
        raise Unauthenticated("Session unavailable") from None

    raw_parent_id = session.get("parentID")
    if type(raw_parent_id) is int:
        parent_id = raw_parent_id
    elif (
        isinstance(raw_parent_id, str)
        and raw_parent_id.isascii()
        and raw_parent_id.isdigit()
    ):
        try:
            parent_id = int(raw_parent_id)
        except (ValueError, OverflowError):
            _clear_invalid_session(request)
            raise Unauthenticated("Invalid session") from None
    else:
        _clear_invalid_session(request)
        raise Unauthenticated("Invalid session")
    if parent_id <= 0:
        _clear_invalid_session(request)
        raise Unauthenticated("Invalid session")

    parent = db.get(Parent, parent_id)
    if parent is None:
        _clear_invalid_session(request)
        raise Unauthenticated("Session account no longer exists")
    return parent


def current_parent_id(
    request: Request,
    db: Session = Depends(get_db),
) -> int:
    return _authenticated_parent(request, db).parentID


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> int:
    parent = _authenticated_parent(request, db)
    if not parent.isAdmin:
        raise Forbidden("Administrator access required")
    return parent.parentID


def require_pin(
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    _authenticated_parent(request, db)
    if request.session.get("pinVerified") is not True:
        raise Forbidden("PIN verification required", ErrorCode.PIN_REQUIRED)


def owned_child(
    childID: int,
    request: Request,
    db: Session = Depends(get_db),
) -> ChildProfile:
    parent = _authenticated_parent(request, db)
    child = db.get(ChildProfile, childID)

    if child is None:
        raise NotFound("Child profile not found")

    if child.parentID != parent.parentID and not parent.isAdmin:
        logger.warning(
            "Ownership violation: parent %s requested child %s",
            parent.parentID,
            childID,
        )
        raise Forbidden("This child profile does not belong to your account")

    return child
