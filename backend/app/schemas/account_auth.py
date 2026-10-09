import re
import uuid

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes.")
    return value


class RegisterCodeRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    _validate_password = field_validator("password")(_validate_bcrypt_password)


class LoginCodeRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    _validate_password = field_validator("password")(_validate_bcrypt_password)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class VerifyCodeRequest(BaseModel):
    challenge_id: str
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("challenge_id")
    @classmethod
    def validate_challenge_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ValueError("The verification request is invalid.") from exc


class ResendCodeRequest(BaseModel):
    challenge_id: str

    @field_validator("challenge_id")
    @classmethod
    def validate_challenge_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ValueError("The verification request is invalid.") from exc


class ResetPasswordRequest(BaseModel):
    challenge_id: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("challenge_id")
    @classmethod
    def validate_challenge_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ValueError("The password reset request is invalid.") from exc

    _validate_password = field_validator("new_password")(_validate_bcrypt_password)


class ParentPinRequest(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")


class ResetParentPinRequest(BaseModel):
    challenge_id: str
    new_pin: str = Field(pattern=r"^\d{4}$")

    @field_validator("challenge_id")
    @classmethod
    def validate_challenge_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, AttributeError) as exc:
            raise ValueError("The PIN reset request is invalid.") from exc

