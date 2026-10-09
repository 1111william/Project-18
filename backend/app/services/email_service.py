import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from backend.app.config import settings
from backend.app.core.responses import ApiError, ErrorCode


logger = logging.getLogger("account.email")

SUBJECTS = {
    "register": "Verify your Project 18 account",
    "login": "Your Project 18 login code",
    "password_reset": "Reset your Project 18 password",
    "child_delete": "Confirm child profile deletion",
}


def send_verification_code(recipient: str, code: str, purpose: str) -> str:
    if settings.EMAIL_DELIVERY != "smtp":
        return "development"

    if not all(
        [
            settings.SMTP_HOST,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        ]
    ):
        raise ApiError(
            503,
            "Email delivery is not configured. Please try again later.",
            ErrorCode.INTERNAL_ERROR,
        )

    message = EmailMessage()
    message["Subject"] = SUBJECTS.get(purpose, "Your Project 18 verification code")
    message["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_FROM_EMAIL))
    message["To"] = recipient
    message.set_content(
        "Your Project 18 verification code is:\n\n"
        f"{code}\n\n"
        "This code expires in 10 minutes. Do not share it with anyone.\n\n"
        "If you did not request this code, you can ignore this email."
    )

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        ) as smtp:
            smtp.ehlo()
            if settings.SMTP_STARTTLS:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Verification email delivery failed")
        raise ApiError(
            503,
            "We could not send the verification code. Please try again.",
            ErrorCode.INTERNAL_ERROR,
        ) from None

    return "smtp"

