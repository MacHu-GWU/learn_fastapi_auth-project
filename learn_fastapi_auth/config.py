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
    access_token_lifetime: int = dataclasses.field()

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
            access_token_lifetime=int(
                os.environ.get("ACCESS_TOKEN_LIFETIME", "3600")
            ),
        )


config = Config.from_env()
"""Singleton configuration instance."""
