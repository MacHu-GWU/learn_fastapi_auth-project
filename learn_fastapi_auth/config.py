# -*- coding: utf-8 -*-

"""
Configuration management module.

Loads environment variables from .env file and provides a centralized Config class
for accessing all application settings.
"""

import os
import dataclasses
from pathlib import Path

from dotenv import load_dotenv


@dataclasses.dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Database
    database_url: str = dataclasses.field()

    # JWT
    secret_key: str = dataclasses.field()

    # SMTP Email
    smtp_host: str = dataclasses.field()
    smtp_port: int = dataclasses.field()
    smtp_tls: bool = dataclasses.field()
    smtp_user: str = dataclasses.field()
    smtp_password: str = dataclasses.field()
    smtp_from: str = dataclasses.field()
    smtp_from_name: str = dataclasses.field()

    # Application
    frontend_url: str = dataclasses.field()
    verification_token_lifetime: int = dataclasses.field()
    reset_password_token_lifetime: int = dataclasses.field()
    access_token_lifetime: int = dataclasses.field()
    refresh_token_lifetime: int = dataclasses.field()
    remember_me_refresh_token_lifetime: int = dataclasses.field()

    # Refresh Token Cookie
    refresh_token_cookie_name: str = dataclasses.field()
    refresh_token_cookie_secure: bool = dataclasses.field()
    refresh_token_cookie_samesite: str = dataclasses.field()

    # Rate Limiting
    rate_limit_login: str = dataclasses.field()
    rate_limit_register: str = dataclasses.field()
    rate_limit_forgot_password: str = dataclasses.field()
    rate_limit_default: str = dataclasses.field()

    # CSRF Protection
    csrf_cookie_name: str = dataclasses.field()
    csrf_cookie_secure: bool = dataclasses.field()
    csrf_cookie_samesite: str = dataclasses.field()

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Load .env file from project root
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)

        return cls(
            # Database
            database_url=os.environ["DATABASE_URL"],
            # JWT
            secret_key=os.environ["SECRET_KEY"],
            # SMTP Email
            smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_tls=os.environ.get("SMTP_TLS", "True").lower() == "true",
            smtp_user=os.environ["SMTP_USER"],
            smtp_password=os.environ["SMTP_PASSWORD"],
            smtp_from=os.environ["SMTP_FROM"],
            smtp_from_name=os.environ.get("SMTP_FROM_NAME", "FastAPI Auth"),
            # Application
            frontend_url=os.environ.get("FRONTEND_URL", "http://localhost:8000"),
            verification_token_lifetime=int(
                os.environ.get("VERIFICATION_TOKEN_LIFETIME", "900")
            ),
            reset_password_token_lifetime=int(
                os.environ.get("RESET_PASSWORD_TOKEN_LIFETIME", "900")
            ),
            access_token_lifetime=int(
                os.environ.get("ACCESS_TOKEN_LIFETIME", "3600")
            ),
            refresh_token_lifetime=int(
                os.environ.get("REFRESH_TOKEN_LIFETIME", "604800")  # 7 days
            ),
            remember_me_refresh_token_lifetime=int(
                os.environ.get("REMEMBER_ME_REFRESH_TOKEN_LIFETIME", "2592000")  # 30 days
            ),
            # Refresh Token Cookie
            refresh_token_cookie_name=os.environ.get(
                "REFRESH_TOKEN_COOKIE_NAME", "refresh_token"
            ),
            refresh_token_cookie_secure=os.environ.get(
                "REFRESH_TOKEN_COOKIE_SECURE", "False"
            ).lower()
            == "true",
            refresh_token_cookie_samesite=os.environ.get(
                "REFRESH_TOKEN_COOKIE_SAMESITE", "lax"
            ),
            # Rate Limiting (default values follow common security practices)
            rate_limit_login=os.environ.get("RATE_LIMIT_LOGIN", "5/minute"),
            rate_limit_register=os.environ.get("RATE_LIMIT_REGISTER", "10/hour"),
            rate_limit_forgot_password=os.environ.get(
                "RATE_LIMIT_FORGOT_PASSWORD", "3/hour"
            ),
            rate_limit_default=os.environ.get("RATE_LIMIT_DEFAULT", "60/minute"),
            # CSRF Protection
            csrf_cookie_name=os.environ.get("CSRF_COOKIE_NAME", "csrftoken"),
            csrf_cookie_secure=os.environ.get("CSRF_COOKIE_SECURE", "False").lower()
            == "true",
            csrf_cookie_samesite=os.environ.get("CSRF_COOKIE_SAMESITE", "lax"),
        )


config = Config.from_env()
"""Singleton configuration instance."""
