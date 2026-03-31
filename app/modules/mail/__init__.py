"""Mail transport and template utilities."""

from app.modules.mail.templates import (
    MailPayload,
    build_password_reset_email,
    build_resend_verification_email,
    build_verification_email,
)
from app.modules.mail.transport import (
    SMTPAuthError,
    SMTPDeliveryError,
    send_mail,
    set_mail_context,
)

__all__ = [
    "MailPayload",
    "SMTPAuthError",
    "SMTPDeliveryError",
    "build_verification_email",
    "build_resend_verification_email",
    "build_password_reset_email",
    "send_mail",
    "set_mail_context",
]
