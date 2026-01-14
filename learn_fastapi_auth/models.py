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
import sqlalchemy as sa
import sqlalchemy.orm as orm

from .database import Base


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

    :param created_at: server_default ensures consistent timestamp even in bulk inserts.
    :param updated_at: onupdate auto-tracks modifications without application code.
    :param firebase_uid: nullable because password-based users don't have Firebase identity.
    :param user_data: One-to-One, cascade delete ensures no orphan records.
    :param tokens: One-to-Many, cascade delete revokes all tokens when user is deleted.
    :param refresh_tokens: One-to-Many, same cascade behavior as tokens.
    """

    __tablename__ = "users"

    # fmt: off
    # Additional fields beyond fastapi-users defaults
    created_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    # Firebase OAuth - stores Firebase UID for users who sign in via Google/Apple
    # Nullable because password-based users don't have a Firebase UID
    firebase_uid: orm.Mapped[str | None] = orm.mapped_column(sa.String(128), unique=True, nullable=True, index=True)

    # Tracks whether user has set their own password
    # True: user registered with email/password OR OAuth user later set a password
    # False: user only signed up via OAuth (has random generated password)
    # This determines if "Change Password" vs "Set Password" is shown
    has_set_password: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, server_default=sa.text("false"))

    # Relationships
    user_data: orm.Mapped[T.Optional["UserData"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    tokens: orm.Mapped[list["Token"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: orm.Mapped[list["RefreshToken"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan")
    # fmt: on


class UserData(Base):
    """
    User-specific data storage.

    Each user has exactly one UserData record containing their text content.

    :param user_id: serves as both FK and PK to enforce One-to-One relationship.
    :param text_value: uses Text type for unlimited length user content.
    :param user: back-reference to parent User for ORM navigation.
    """

    __tablename__ = "user_data"

    # fmt: off
    user_id: orm.Mapped[uuid.UUID] = orm.mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    text_value: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")
    created_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    # Relationship back to User
    user: orm.Mapped["User"] = orm.relationship(back_populates="user_data")
    # fmt: on


class Token(Base):
    """
    JWT access token storage.

    Stores tokens in database for validation and revocation support.

    :param token: uses token string as PK for O(1) lookup during validation.
    :param expires_at: enables efficient cleanup of expired tokens via scheduled job.
    :param user: Many-to-One back-reference, ondelete CASCADE auto-revokes on user deletion.
    """

    __tablename__ = "tokens"

    # fmt: off
    token: orm.Mapped[str] = orm.mapped_column(sa.String(500), primary_key=True)
    user_id: orm.Mapped[uuid.UUID] = orm.mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"))
    created_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    expires_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True))

    # Relationship back to User
    user: orm.Mapped["User"] = orm.relationship(back_populates="tokens")
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

    :param token: uses token string as PK for O(1) lookup during refresh.
    :param expires_at: longer TTL than access tokens, enables periodic re-auth.
    :param user: Many-to-One back-reference, ondelete CASCADE revokes all on user deletion.
    """

    __tablename__ = "refresh_tokens"

    # fmt: off
    token: orm.Mapped[str] = orm.mapped_column(sa.String(500), primary_key=True)
    user_id: orm.Mapped[uuid.UUID] = orm.mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"))
    created_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    expires_at: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime(timezone=True))

    # Relationship back to User
    user: orm.Mapped["User"] = orm.relationship(back_populates="refresh_tokens")
    # fmt: on
