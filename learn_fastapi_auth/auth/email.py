# -*- coding: utf-8 -*-

"""
Email sending functionality.

Provides async email sending via SMTP for:
- Email verification
- Password reset
"""

import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib

from ..logger import logger
from ..one.api import one

# Template directory
_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(name: str, **kwargs: str) -> str:
    """Load HTML template and substitute placeholders."""
    template_path = _TEMPLATE_DIR / name
    content = template_path.read_text(encoding="utf-8")
    return content.format(**kwargs)


# =============================================================================
# Verification Email
# =============================================================================
def get_verification_email_html(verification_url: str) -> str:
    """Generate HTML content for verification email."""
    return _load_template("verification_email.html", verification_url=verification_url)


def get_verification_email_text(verification_url: str) -> str:
    """Generate plain text content for verification email."""
    return f"""Verify Your Email

Thanks for signing up! Please verify your email address by visiting the link below:

{verification_url}

This link will expire in 15 minutes.

If you didn't create an account, you can safely ignore this email.
"""


# =============================================================================
# Password Reset Email
# =============================================================================
def get_password_reset_email_html(reset_url: str) -> str:
    """Generate HTML content for password reset email."""
    return _load_template("password_reset_email.html", reset_url=reset_url)


def get_password_reset_email_text(reset_url: str) -> str:
    """Generate plain text content for password reset email."""
    return f"""Reset Your Password

We received a request to reset your password. Visit the link below to choose a new one:

{reset_url}

This link will expire in 15 minutes.

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
"""


# =============================================================================
# Email Sending
# =============================================================================
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """
    Send an email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body of the email
        text_content: Plain text body of the email

    Returns:
        True if email was sent successfully, False otherwise
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{one.env.smtp_from_name} <{one.env.smtp_from}>"
    message["To"] = to_email

    # Add plain text and HTML parts
    part1 = MIMEText(text_content, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)

    try:
        # Create SSL context
        context = ssl.create_default_context()

        # Connect and send
        await aiosmtplib.send(
            message,
            hostname=one.env.smtp_host,
            port=one.env.smtp_port,
            username=one.env.smtp_user,
            password=one.env.smtp_password,
            start_tls=one.env.smtp_tls,
            tls_context=context,
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_verification_email(email: str, token: str) -> bool:
    """
    Send email verification link to user.

    Args:
        email: User's email address
        token: Verification token

    Returns:
        True if email was sent successfully, False otherwise
    """
    verification_url = f"{one.env.final_frontend_url}/auth/verify-email?token={token}"

    return await send_email(
        to_email=email,
        subject="Verify Your Email Address",
        html_content=get_verification_email_html(verification_url),
        text_content=get_verification_email_text(verification_url),
    )


async def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send password reset link to user.

    Args:
        email: User's email address
        token: Password reset token

    Returns:
        True if email was sent successfully, False otherwise
    """
    reset_url = f"{one.env.final_frontend_url}/auth/reset-password?token={token}"

    return await send_email(
        to_email=email,
        subject="Reset Your Password",
        html_content=get_password_reset_email_html(reset_url),
        text_content=get_password_reset_email_text(reset_url),
    )
