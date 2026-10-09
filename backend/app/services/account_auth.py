import hashlib
import secrets
import threading
import time
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.responses import ApiError, ErrorCode
from backend.app.core.security import hash_password, verify_password
from backend.app.models import Parent


CODE_LIFETIME_SECONDS = 10 * 60
RESEND_COOLDOWN_SECONDS = 30
MAX_CODE_ATTEMPTS = 5


@dataclass
class RegistrationChallenge:
    challenge_id: str
    email: str
    password_hash: str
    code_hash: str
    expires_at: int
    resend_at: int
    attempts_remaining: int = MAX_CODE_ATTEMPTS
    purpose: str = "register"
    parent_id: int | None = None
    child_id: int | None = None
    reset_authorized: bool = False


class RegistrationChallengeStore:
    """Temporary local store for the first registration slice.

    A persistent database-backed challenge table will replace this store when
    registration verification is implemented.
    """

    def __init__(self):
        self._by_id: dict[str, RegistrationChallenge] = {}
        self._latest_by_email: dict[str, str] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _hash_code(challenge_id: str, code: str) -> str:
        return hashlib.sha256(f"{challenge_id}:{code}".encode("utf-8")).hexdigest()

    def create(self, email: str, password: str) -> tuple[RegistrationChallenge, str]:
        return self._create_challenge(
            email=email,
            password_hash=hash_password(password),
            purpose="register",
        )

    def create_password_reset(self, email: str, parent_id: int) -> tuple[RegistrationChallenge, str]:
        return self._create_challenge(
            email=email,
            password_hash="",
            purpose="password_reset",
            parent_id=parent_id,
        )

    def create_child_delete(
        self,
        email: str,
        parent_id: int,
        child_id: int,
    ) -> tuple[RegistrationChallenge, str]:
        return self._create_challenge(
            email=email,
            password_hash="",
            purpose="child_delete",
            parent_id=parent_id,
            child_id=child_id,
        )

    def _create_challenge(
        self,
        email: str,
        password_hash: str,
        purpose: str,
        parent_id: int | None = None,
        child_id: int | None = None,
    ) -> tuple[RegistrationChallenge, str]:
        now = int(time.time())

        with self._lock:
            previous_id = self._latest_by_email.get(email)
            previous = self._by_id.get(previous_id) if previous_id else None
            if previous and previous.resend_at > now:
                wait_seconds = previous.resend_at - now
                raise ApiError(
                    429,
                    f"Please wait {wait_seconds} seconds before requesting another code.",
                    ErrorCode.VALIDATION_FAILED,
                    ["email"],
                )

            challenge_id = str(uuid.uuid4())
            code = f"{secrets.randbelow(1_000_000):06d}"
            challenge = RegistrationChallenge(
                challenge_id=challenge_id,
                email=email,
                password_hash=password_hash,
                code_hash=self._hash_code(challenge_id, code),
                expires_at=now + CODE_LIFETIME_SECONDS,
                resend_at=now + RESEND_COOLDOWN_SECONDS,
                purpose=purpose,
                parent_id=parent_id,
                child_id=child_id,
            )
            self._by_id[challenge_id] = challenge
            self._latest_by_email[email] = challenge_id
            return challenge, code

    def verify(self, challenge_id: str, code: str) -> RegistrationChallenge:
        now = int(time.time())

        with self._lock:
            challenge = self._by_id.get(challenge_id)
            if challenge is None:
                raise ApiError(
                    400,
                    "This verification request is no longer available. Request a new code.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )
            if challenge.expires_at <= now:
                self._remove(challenge)
                raise ApiError(
                    400,
                    "The verification code has expired. Request a new code.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )
            if challenge.attempts_remaining <= 0:
                raise ApiError(
                    400,
                    "Too many incorrect attempts. Request a new code.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )

            submitted_hash = self._hash_code(challenge_id, code)
            if not secrets.compare_digest(challenge.code_hash, submitted_hash):
                challenge.attempts_remaining -= 1
                if challenge.attempts_remaining == 0:
                    message = "Too many incorrect attempts. Request a new code."
                else:
                    message = "The verification code is incorrect."
                raise ApiError(
                    400,
                    message,
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )

            return challenge

    def get(self, challenge_id: str) -> RegistrationChallenge:
        with self._lock:
            challenge = self._by_id.get(challenge_id)
            if challenge is None:
                raise ApiError(
                    400,
                    "This verification request is no longer available. Start again.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )
            return challenge

    def resend(self, challenge_id: str) -> tuple[RegistrationChallenge, str]:
        now = int(time.time())

        with self._lock:
            challenge = self._by_id.get(challenge_id)
            if challenge is None:
                raise ApiError(
                    400,
                    "This verification request is no longer available. Start again.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )
            if challenge.resend_at > now:
                wait_seconds = challenge.resend_at - now
                raise ApiError(
                    429,
                    f"Please wait {wait_seconds} seconds before requesting another code.",
                    ErrorCode.VALIDATION_FAILED,
                    ["code"],
                )

            code = f"{secrets.randbelow(1_000_000):06d}"
            challenge.code_hash = self._hash_code(challenge.challenge_id, code)
            challenge.expires_at = now + CODE_LIFETIME_SECONDS
            challenge.resend_at = now + RESEND_COOLDOWN_SECONDS
            challenge.attempts_remaining = MAX_CODE_ATTEMPTS
            challenge.reset_authorized = False
            return challenge, code

    def consume(self, challenge_id: str) -> None:
        with self._lock:
            challenge = self._by_id.get(challenge_id)
            if challenge is not None:
                self._remove(challenge)

    def authorize_password_reset(self, challenge_id: str, code: str) -> RegistrationChallenge:
        challenge = self.verify(challenge_id, code)
        if challenge.purpose != "password_reset" or challenge.parent_id is None:
            raise ApiError(
                400,
                "The password reset request is invalid.",
                ErrorCode.VALIDATION_FAILED,
                ["code"],
            )
        with self._lock:
            challenge.reset_authorized = True
            challenge.code_hash = ""
        return challenge

    def get_authorized_password_reset(self, challenge_id: str) -> RegistrationChallenge:
        now = int(time.time())
        with self._lock:
            challenge = self._by_id.get(challenge_id)
            if (
                challenge is None
                or challenge.purpose != "password_reset"
                or challenge.parent_id is None
                or not challenge.reset_authorized
                or challenge.expires_at <= now
            ):
                raise ApiError(
                    400,
                    "The password reset request has expired. Start again.",
                    ErrorCode.VALIDATION_FAILED,
                )
            return challenge

    def _remove(self, challenge: RegistrationChallenge) -> None:
        self._by_id.pop(challenge.challenge_id, None)
        if self._latest_by_email.get(challenge.email) == challenge.challenge_id:
            self._latest_by_email.pop(challenge.email, None)


def email_display_name(email: str) -> str:
    local_part = email.split("@", 1)[0].strip()
    return (local_part or "Parent")[:100]


def create_parent_account(db: Session, challenge: RegistrationChallenge) -> Parent:
    existing = db.scalar(select(Parent).where(Parent.email == challenge.email))
    if existing is not None:
        raise ApiError(
            409,
            "An account with this email already exists.",
            ErrorCode.VALIDATION_FAILED,
            ["email"],
        )

    parent = Parent(
        email=challenge.email,
        passwordHash=challenge.password_hash,
        displayName=email_display_name(challenge.email),
        isAdmin=False,
    )
    db.add(parent)
    try:
        db.commit()
        db.refresh(parent)
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409,
            "An account with this email already exists.",
            ErrorCode.VALIDATION_FAILED,
            ["email"],
        ) from exc
    return parent


def authenticate_parent(db: Session, email: str, password: str) -> Parent:
    parent = db.scalar(select(Parent).where(Parent.email == email))
    if parent is None or not verify_password(password, parent.passwordHash):
        raise ApiError(
            401,
            "Email or password is incorrect.",
            ErrorCode.UNAUTHENTICATED,
            ["password"],
        )
    return parent


def find_parent_by_email(db: Session, email: str) -> Parent:
    parent = db.scalar(select(Parent).where(Parent.email == email))
    if parent is None:
        raise ApiError(
            404,
            "No account was found for this email address.",
            ErrorCode.NOT_FOUND,
            ["email"],
        )
    return parent


def get_parent(db: Session, parent_id: int) -> Parent:
    parent = db.get(Parent, parent_id)
    if parent is None:
        raise ApiError(401, "Sign in required", ErrorCode.UNAUTHENTICATED)
    return parent


def reset_parent_password(db: Session, parent: Parent, new_password: str) -> None:
    parent.passwordHash = hash_password(new_password)
    db.add(parent)
    db.commit()


registration_challenges = RegistrationChallengeStore()

