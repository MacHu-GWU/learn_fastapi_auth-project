# -*- coding: utf-8 -*-

"""
SQLAlchemy ORM models.

Defines the database models for:

- :class:`User`: Authentication user (managed by fastapi-users)
- :class:`UserData`: User-specific text data
- :class:`Token`: JWT access tokens stored in database
- :class:`RefreshToken`: Long-lived tokens for obtaining new access tokens

Model Relationships:

- :class:`User` ↔ :class`UserData`: One-to-One. Each user has exactly one UserData record for their profile content.
- :class:`User` ↔ :class`Token`: One-to-Many. A user can have multiple active access tokens (multi-device login).
- :class:`User` ↔ :class`RefreshToken`: One-to-Many. A user can have multiple refresh tokens for token rotation across devices.
"""

from datetime import datetime
import typing as T
import uuid

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learn_fastapi_auth.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User model managed by fastapi-users.

    Inherits from SQLAlchemyBaseUserTableUUID which provides:
    - id: UUID primary key
    - email: unique email address
    - hashed_password: password hash
    - is_active: account active status
    - is_superuser: admin status
    - is_verified: email verification status
    """

    __tablename__ = "users"

    # fmt: off
    # Additional fields beyond fastapi-users defaults
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Firebase OAuth - stores Firebase UID for users who sign in via Google/Apple
    # Nullable because password-based users don't have a Firebase UID
    firebase_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)

    # Relationships
    user_data: Mapped[T.Optional["UserData"]] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    tokens: Mapped[list["Token"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    # fmt: on


class UserData(Base):
    """
    User-specific data storage.

    Each user has exactly one UserData record containing their text content.
    """

    __tablename__ = "user_data"

    # fmt: off
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    text_value: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="user_data")
    # fmt: on


class Token(Base):
    """
    JWT access token storage.

    Stores tokens in database for validation and revocation support.
    """

    __tablename__ = "tokens"

    # fmt: off
    token: Mapped[str] = mapped_column(String(500), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="tokens")
    # fmt: on


class RefreshToken(Base):
    """
    Refresh token storage for token refresh mechanism.

    Refresh tokens are long-lived tokens used to obtain new access tokens
    without requiring the user to re-authenticate.

    Stored in database for:
    - Validation on refresh requests
    - Revocation support (logout from all devices)
    - Token rotation (optional security enhancement)
    """

    __tablename__ = "refresh_tokens"

    # fmt: off
    token: Mapped[str] = mapped_column(String(500), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
    # fmt: on
