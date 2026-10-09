import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode, ok
from backend.app.core.security import hash_password, verify_password
from backend.app.database import get_db
from backend.app.middleware import current_parent_id
from backend.app.schemas.account_auth import (
    ForgotPasswordRequest,
    LoginCodeRequest,
    ParentPinRequest,
    RegisterCodeRequest,
    ResendCodeRequest,
    ResetPasswordRequest,
    VerifyCodeRequest,
)
from backend.app.services.account_auth import (
    authenticate_parent,
    create_parent_account,
    find_parent_by_email,
    get_parent,
    registration_challenges,
    reset_parent_password,
)
from backend.app.services.email_service import send_verification_code


router = APIRouter()


def verification_challenge_response(challenge, code: str):
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


@router.get("/config")
def account_config():
    return ok({"development_codes": settings.AUTH_DEVELOPMENT_CODES})


@router.post("/register")
def request_registration_code(payload: RegisterCodeRequest):
    challenge, code = registration_challenges.create(payload.email, payload.password)
    return verification_challenge_response(challenge, code)


@router.post("/login")
def login(
    payload: LoginCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    parent = authenticate_parent(db, payload.email, payload.password)

    request.session.clear()
    request.session["parentID"] = parent.parentID
    request.session["isAdmin"] = bool(parent.isAdmin)
    request.session["pinVerified"] = False

    return ok(
        {
            "user": {
                "parentID": parent.parentID,
                "email": parent.email,
                "displayName": parent.displayName,
                "hasPin": bool(parent.pinHash),
            }
        }
    )


@router.post("/forgot-password")
def request_password_reset_code(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    parent = find_parent_by_email(db, payload.email)
    challenge, code = registration_challenges.create_password_reset(parent.email, parent.parentID)
    return verification_challenge_response(challenge, code)


@router.post("/resend-code")
def resend_verification_code(payload: ResendCodeRequest):
    challenge, code = registration_challenges.resend(payload.challenge_id)
    return verification_challenge_response(challenge, code)


@router.post("/verify-code")
def verify_registration_code(
    payload: VerifyCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    pending = registration_challenges.get(payload.challenge_id)
    if pending.purpose == "password_reset":
        challenge = registration_challenges.authorize_password_reset(payload.challenge_id, payload.code)
        return ok({"password_reset": True, "challenge_id": challenge.challenge_id})

    challenge = registration_challenges.verify(payload.challenge_id, payload.code)
    if challenge.purpose != "register":
        raise ApiError(400, "The verification request is invalid.", ErrorCode.VALIDATION_FAILED, ["code"])
    parent = create_parent_account(db, challenge)
    registration_challenges.consume(challenge.challenge_id)

    request.session.clear()
    request.session["parentID"] = parent.parentID
    request.session["isAdmin"] = bool(parent.isAdmin)
    request.session["pinVerified"] = False

    return ok(
        {
            "user": {
                "parentID": parent.parentID,
                "email": parent.email,
                "displayName": parent.displayName,
                "hasPin": bool(parent.pinHash),
            }
        }
    )


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    challenge = registration_challenges.get_authorized_password_reset(payload.challenge_id)
    parent = get_parent(db, challenge.parent_id)
    if parent.email != challenge.email:
        raise ApiError(400, "The password reset request is invalid.", ErrorCode.VALIDATION_FAILED)
    reset_parent_password(db, parent, payload.new_password)
    registration_challenges.consume(challenge.challenge_id)
    request.session.clear()
    return ok({"password_reset": True})


@router.get("/me")
def current_account(request: Request, db: Session = Depends(get_db)):
    parent_id = request.session.get("parentID")
    if not parent_id:
        raise ApiError(401, "Sign in required", ErrorCode.UNAUTHENTICATED)
    parent = get_parent(db, int(parent_id))
    return ok(
        {
            "parentID": parent.parentID,
            "email": parent.email,
            "displayName": parent.displayName,
            "hasPin": bool(parent.pinHash),
        }
    )


@router.put("/pin")
def set_parent_pin(
    payload: ParentPinRequest,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    parent = get_parent(db, parent_id)
    if parent.pinHash:
        raise ApiError(
            409,
            "A parent PIN has already been set.",
            ErrorCode.VALIDATION_FAILED,
            ["pin"],
        )
    parent.pinHash = hash_password(payload.pin)
    db.add(parent)
    db.commit()
    return ok({"pin_set": True})


@router.post("/pin/verify")
def verify_parent_pin(
    payload: ParentPinRequest,
    request: Request,
    parent_id: int = Depends(current_parent_id),
    db: Session = Depends(get_db),
):
    now = int(time.time())
    locked_until = int(request.session.get("pinLockedUntil", 0))
    if locked_until > now:
        raise ApiError(
            429,
            f"Too many incorrect attempts. Try again in {locked_until - now} seconds.",
            ErrorCode.PIN_REQUIRED,
            ["pin"],
        )

    parent = get_parent(db, parent_id)
    if not parent.pinHash:
        raise ApiError(409, "Set a parent PIN first.", ErrorCode.PIN_REQUIRED, ["pin"])

    if not verify_password(payload.pin, parent.pinHash):
        attempts = int(request.session.get("pinAttempts", 0)) + 1
        if attempts >= 5:
            request.session["pinAttempts"] = 0
            request.session["pinLockedUntil"] = now + 60
            message = "Too many incorrect attempts. Try again in 60 seconds."
        else:
            request.session["pinAttempts"] = attempts
            message = f"PIN is incorrect. {5 - attempts} attempts remaining."
        raise ApiError(400, message, ErrorCode.PIN_REQUIRED, ["pin"])

    request.session["pinVerified"] = True
    request.session["pinAttempts"] = 0
    request.session.pop("pinLockedUntil", None)
    return ok({"pin_verified": True})


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return ok({"signed_out": True})

