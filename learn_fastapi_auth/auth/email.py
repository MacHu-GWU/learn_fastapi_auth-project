# -*- coding: utf-8 -*-

"""
Email sending functionality.

Provides async email sending via SMTP for:
- Email verification
- Password reset (future)
"""

import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from learn_fastapi_auth.one.api import one


def get_verification_email_html(verification_url: str) -> str:
    """Generate HTML content for verification email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>验证您的邮箱地址</h2>
        <p>欢迎注册！</p>
        <p>请点击下方按钮验证您的邮箱地址：</p>
        <p>
            <a href="{verification_url}" class="button">验证邮箱</a>
        </p>
        <p>或复制此链接到浏览器：<br>{verification_url}</p>
        <p>此链接将在 15 分钟后过期。</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            如果您没有注册此账户，请忽略此邮件。
        </p>
    </div>
</body>
</html>"""


def get_verification_email_text(verification_url: str) -> str:
    """Generate plain text content for verification email."""
    return f"""验证您的邮箱地址

欢迎注册！

请点击下方链接验证您的邮箱地址：
{verification_url}

此链接将在 15 分钟后过期。

如果您没有注册此账户，请忽略此邮件。
"""


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
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
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
        subject="验证您的邮箱地址",
        html_content=get_verification_email_html(verification_url),
        text_content=get_verification_email_text(verification_url),
    )


# =============================================================================
# Password Reset Email
# =============================================================================
def get_password_reset_email_html(reset_url: str) -> str:
    """Generate HTML content for password reset email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #dc3545;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>重置您的密码</h2>
        <p>您请求重置密码。</p>
        <p>请点击下方按钮设置新密码：</p>
        <p>
            <a href="{reset_url}" class="button">重置密码</a>
        </p>
        <p>或复制此链接到浏览器：<br>{reset_url}</p>
        <p>此链接将在 15 分钟后过期。</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            如果您没有请求重置密码，请忽略此邮件。您的密码不会被更改。
        </p>
    </div>
</body>
</html>"""


def get_password_reset_email_text(reset_url: str) -> str:
    """Generate plain text content for password reset email."""
    return f"""重置您的密码

您请求重置密码。

请点击下方链接设置新密码：
{reset_url}

此链接将在 15 分钟后过期。

如果您没有请求重置密码，请忽略此邮件。您的密码不会被更改。
"""


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
        subject="重置您的密码",
        html_content=get_password_reset_email_html(reset_url),
        text_content=get_password_reset_email_text(reset_url),
    )
