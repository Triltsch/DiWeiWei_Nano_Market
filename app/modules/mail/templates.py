"""Mail payload templates for auth-related messages."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MailPayload:
    """Rendered mail content ready for transport delivery."""

    subject: str
    body_html: str
    body_text: str
    message_type: str


def build_verification_email(username: str, verification_url: str) -> MailPayload:
    """Build the registration verification email payload."""
    safe_username = username.strip() or "there"
    subject = "Verify your email address"
    body_text = (
        f"Hello {safe_username},\n\n"
        "please verify your email address by opening this link:\n"
        f"{verification_url}\n\n"
        "If you did not create an account, you can ignore this message."
    )
    body_html = (
        f"<p>Hello {safe_username},</p>"
        "<p>Please verify your email address by opening this link:</p>"
        f'<p><a href="{verification_url}">Verify email</a></p>'
        "<p>If you did not create an account, you can ignore this message.</p>"
    )
    return MailPayload(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        message_type="verification",
    )


def build_resend_verification_email(username: str, verification_url: str) -> MailPayload:
    """Build the resend-verification email payload."""
    safe_username = username.strip() or "there"
    subject = "Your new verification link"
    body_text = (
        f"Hello {safe_username},\n\n"
        "you requested a new verification link. Open this link to verify your email:\n"
        f"{verification_url}\n\n"
        "If you did not request this, you can ignore this message."
    )
    body_html = (
        f"<p>Hello {safe_username},</p>"
        "<p>You requested a new verification link. Open this link to verify your email:</p>"
        f'<p><a href="{verification_url}">Verify email</a></p>'
        "<p>If you did not request this, you can ignore this message.</p>"
    )
    return MailPayload(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        message_type="resend_verification",
    )


def build_password_reset_email(username: str, reset_url: str) -> MailPayload:
    """Build the optional password-reset email payload."""
    safe_username = username.strip() or "there"
    subject = "Reset your password"
    body_text = (
        f"Hello {safe_username},\n\n"
        "you can reset your password by opening this link:\n"
        f"{reset_url}\n\n"
        "If you did not request a reset, ignore this message."
    )
    body_html = (
        f"<p>Hello {safe_username},</p>"
        "<p>You can reset your password by opening this link:</p>"
        f'<p><a href="{reset_url}">Reset password</a></p>'
        "<p>If you did not request a reset, ignore this message.</p>"
    )
    return MailPayload(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        message_type="password_reset",
    )
