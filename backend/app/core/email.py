# launchkit/backend/app/core/email.py
"""
Abstracted email service. SMTP default, swappable to Resend/SendGrid
without changing any callers. All methods are fire-and-forget safe —
they log errors internally and never raise to the caller.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as exc:
        # Never raise — email failure must not break the request
        logger.error(f"Failed to send email to {to}: {exc}")


def send_email(to: str, subject: str, html: str) -> None:
    """Entry point — routes to configured backend."""
    if settings.EMAIL_BACKEND == "smtp":
        _send_smtp(to, subject, html)
    else:
        logger.warning(f"Unknown EMAIL_BACKEND '{settings.EMAIL_BACKEND}' — email not sent")


# ── Email templates ───────────────────────────────────────────────────────────

def send_email_verification(to: str, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Verify your email</h2>
        <p>Click the link below to verify your email address. This link expires in 24 hours.</p>
        <a href="{verify_url}" style="
            display: inline-block;
            padding: 12px 24px;
            background: #00C896;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 16px 0;
        ">Verify Email</a>
        <p>Or copy this link: {verify_url}</p>
        <p style="color: #888;">If you didn't create an account, ignore this email.</p>
    </div>
    """
    send_email(to, "Verify your email — MeetingMind", html)


def send_password_reset(to: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Reset your password</h2>
        <p>Click the link below to reset your password. This link expires in 1 hour.</p>
        <a href="{reset_url}" style="
            display: inline-block;
            padding: 12px 24px;
            background: #00C896;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 16px 0;
        ">Reset Password</a>
        <p>Or copy this link: {reset_url}</p>
        <p style="color: #888;">If you didn't request this, ignore this email. Your password won't change.</p>
    </div>
    """
    send_email(to, "Reset your password — MeetingMind", html)