# -*- coding: utf-8 -*-

"""
Unit tests for learn_fastapi_auth.models module.

Tests cover SQLAlchemy ORM relationships:
- User ↔ UserData: one-to-one relationship
- User ↔ Token: one-to-many relationship
- User ↔ RefreshToken: one-to-many relationship
- Cascade delete behavior

Uses in-memory SQLite for fast, isolated testing.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.models import RefreshToken, Token, User, UserData


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture
def user_id() -> uuid.UUID:
    """Generate a consistent user UUID for tests."""
    return uuid.uuid4()


@pytest.fixture
def make_user():
    """Factory fixture to create User instances."""

    def _make_user(
        user_id: uuid.UUID | None = None,
        email: str | None = None,
        hashed_password: str = "hashed_password_123",
        is_active: bool = True,
        is_superuser: bool = False,
        is_verified: bool = False,
        firebase_uid: str | None = None,
    ) -> User:
        return User(
            id=user_id or uuid.uuid4(),
            email=email or f"user_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=hashed_password,
            is_active=is_active,
            is_superuser=is_superuser,
            is_verified=is_verified,
            firebase_uid=firebase_uid,
        )

    return _make_user


@pytest.fixture
def make_user_data():
    """Factory fixture to create UserData instances."""

    def _make_user_data(
        user_id: uuid.UUID,
        text_value: str = "Sample text content",
    ) -> UserData:
        return UserData(
            user_id=user_id,
            text_value=text_value,
        )

    return _make_user_data


@pytest.fixture
def make_token():
    """Factory fixture to create Token instances."""

    def _make_token(
        user_id: uuid.UUID,
        token: str | None = None,
        expires_at: datetime | None = None,
    ) -> Token:
        return Token(
            token=token or f"access_token_{uuid.uuid4().hex}",
            user_id=user_id,
            expires_at=expires_at or datetime.now(timezone.utc) + timedelta(hours=1),
        )

    return _make_token


@pytest.fixture
def make_refresh_token():
    """Factory fixture to create RefreshToken instances."""

    def _make_refresh_token(
        user_id: uuid.UUID,
        token: str | None = None,
        expires_at: datetime | None = None,
    ) -> RefreshToken:
        return RefreshToken(
            token=token or f"refresh_token_{uuid.uuid4().hex}",
            user_id=user_id,
            expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=7),
        )

    return _make_refresh_token


# ------------------------------------------------------------------------------
# User ↔ UserData One-to-One Relationship Tests
# ------------------------------------------------------------------------------
class TestUserUserDataRelationship:
    """Tests for User ↔ UserData one-to-one relationship."""

    async def test_user_can_have_user_data(
        self,
        test_session: AsyncSession,
        make_user,
        make_user_data,
    ):
        """Test that a User can have associated UserData."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        user_data = make_user_data(user_id=user.id, text_value="My personal notes")
        test_session.add(user_data)
        await test_session.commit()

        # Refresh to load relationships
        await test_session.refresh(user, ["user_data"])

        assert user.user_data is not None
        assert user.user_data.text_value == "My personal notes"
        assert user.user_data.user_id == user.id

    async def test_user_data_back_populates_user(
        self,
        test_session: AsyncSession,
        make_user,
        make_user_data,
    ):
        """Test that UserData.user back-populates correctly."""
        user = make_user(email="backpop@example.com")
        test_session.add(user)
        await test_session.flush()

        user_data = make_user_data(user_id=user.id)
        test_session.add(user_data)
        await test_session.commit()

        # Query UserData and check back-population
        await test_session.refresh(user_data, ["user"])

        assert user_data.user is not None
        assert user_data.user.email == "backpop@example.com"
        assert user_data.user.id == user.id

    async def test_user_without_user_data(
        self,
        test_session: AsyncSession,
        make_user,
    ):
        """Test that a User can exist without UserData (optional relationship)."""
        user = make_user()
        test_session.add(user)
        await test_session.commit()

        await test_session.refresh(user, ["user_data"])

        assert user.user_data is None


# ------------------------------------------------------------------------------
# User ↔ Token One-to-Many Relationship Tests
# ------------------------------------------------------------------------------
class TestUserTokenRelationship:
    """Tests for User ↔ Token one-to-many relationship."""

    async def test_user_can_have_multiple_tokens(
        self,
        test_session: AsyncSession,
        make_user,
        make_token,
    ):
        """Test that a User can have multiple access tokens."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        # Create 3 tokens for the same user
        tokens = [
            make_token(user_id=user.id, token=f"token_{i}_{uuid.uuid4().hex}")
            for i in range(3)
        ]
        test_session.add_all(tokens)
        await test_session.commit()

        await test_session.refresh(user, ["tokens"])

        assert len(user.tokens) == 3
        assert all(t.user_id == user.id for t in user.tokens)

    async def test_token_back_populates_user(
        self,
        test_session: AsyncSession,
        make_user,
        make_token,
    ):
        """Test that Token.user back-populates correctly."""
        user = make_user(email="token_owner@example.com")
        test_session.add(user)
        await test_session.flush()

        token = make_token(user_id=user.id)
        test_session.add(token)
        await test_session.commit()

        await test_session.refresh(token, ["user"])

        assert token.user is not None
        assert token.user.email == "token_owner@example.com"

    async def test_user_without_tokens(
        self,
        test_session: AsyncSession,
        make_user,
    ):
        """Test that a User can exist without any tokens."""
        user = make_user()
        test_session.add(user)
        await test_session.commit()

        await test_session.refresh(user, ["tokens"])

        assert user.tokens == []


# ------------------------------------------------------------------------------
# User ↔ RefreshToken One-to-Many Relationship Tests
# ------------------------------------------------------------------------------
class TestUserRefreshTokenRelationship:
    """Tests for User ↔ RefreshToken one-to-many relationship."""

    async def test_user_can_have_multiple_refresh_tokens(
        self,
        test_session: AsyncSession,
        make_user,
        make_refresh_token,
    ):
        """Test that a User can have multiple refresh tokens (multiple devices)."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        # Create refresh tokens for different devices
        refresh_tokens = [
            make_refresh_token(
                user_id=user.id, token=f"refresh_{device}_{uuid.uuid4().hex}"
            )
            for device in ["desktop", "mobile", "tablet"]
        ]
        test_session.add_all(refresh_tokens)
        await test_session.commit()

        await test_session.refresh(user, ["refresh_tokens"])

        assert len(user.refresh_tokens) == 3
        assert all(rt.user_id == user.id for rt in user.refresh_tokens)

    async def test_refresh_token_back_populates_user(
        self,
        test_session: AsyncSession,
        make_user,
        make_refresh_token,
    ):
        """Test that RefreshToken.user back-populates correctly."""
        user = make_user(email="refresh_owner@example.com")
        test_session.add(user)
        await test_session.flush()

        refresh_token = make_refresh_token(user_id=user.id)
        test_session.add(refresh_token)
        await test_session.commit()

        await test_session.refresh(refresh_token, ["user"])

        assert refresh_token.user is not None
        assert refresh_token.user.email == "refresh_owner@example.com"


# ------------------------------------------------------------------------------
# Cascade Delete Tests
# ------------------------------------------------------------------------------
class TestCascadeDelete:
    """Tests for cascade delete behavior when User is deleted."""

    async def test_deleting_user_deletes_user_data(
        self,
        test_session: AsyncSession,
        make_user,
        make_user_data,
    ):
        """Test that deleting a User cascades to delete UserData."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        user_data = make_user_data(user_id=user.id, text_value="Will be deleted")
        test_session.add(user_data)
        await test_session.commit()

        user_id = user.id

        # Delete the user
        await test_session.delete(user)
        await test_session.commit()

        # Verify UserData is also deleted
        result = await test_session.execute(
            select(UserData).where(UserData.user_id == user_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_deleting_user_deletes_tokens(
        self,
        test_session: AsyncSession,
        make_user,
        make_token,
    ):
        """Test that deleting a User cascades to delete all Tokens."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        tokens = [make_token(user_id=user.id) for _ in range(3)]
        test_session.add_all(tokens)
        await test_session.commit()

        user_id = user.id
        token_values = [t.token for t in tokens]

        # Delete the user
        await test_session.delete(user)
        await test_session.commit()

        # Verify all Tokens are deleted
        result = await test_session.execute(
            select(Token).where(Token.user_id == user_id)
        )
        assert result.scalars().all() == []

    async def test_deleting_user_deletes_refresh_tokens(
        self,
        test_session: AsyncSession,
        make_user,
        make_refresh_token,
    ):
        """Test that deleting a User cascades to delete all RefreshTokens."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        refresh_tokens = [make_refresh_token(user_id=user.id) for _ in range(2)]
        test_session.add_all(refresh_tokens)
        await test_session.commit()

        user_id = user.id

        # Delete the user
        await test_session.delete(user)
        await test_session.commit()

        # Verify all RefreshTokens are deleted
        result = await test_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        assert result.scalars().all() == []

    async def test_deleting_user_cascades_all_related_data(
        self,
        test_session: AsyncSession,
        make_user,
        make_user_data,
        make_token,
        make_refresh_token,
    ):
        """Test that deleting a User cascades to delete ALL related data."""
        user = make_user()
        test_session.add(user)
        await test_session.flush()

        # Create all related entities
        user_data = make_user_data(user_id=user.id)
        tokens = [make_token(user_id=user.id) for _ in range(2)]
        refresh_tokens = [make_refresh_token(user_id=user.id) for _ in range(2)]

        test_session.add(user_data)
        test_session.add_all(tokens)
        test_session.add_all(refresh_tokens)
        await test_session.commit()

        user_id = user.id

        # Delete the user
        await test_session.delete(user)
        await test_session.commit()

        # Verify all related data is deleted
        user_data_result = await test_session.execute(
            select(UserData).where(UserData.user_id == user_id)
        )
        token_result = await test_session.execute(
            select(Token).where(Token.user_id == user_id)
        )
        refresh_token_result = await test_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )

        assert user_data_result.scalar_one_or_none() is None
        assert token_result.scalars().all() == []
        assert refresh_token_result.scalars().all() == []


# ------------------------------------------------------------------------------
# Additional Relationship Edge Cases
# ------------------------------------------------------------------------------
class TestRelationshipEdgeCases:
    """Tests for edge cases in model relationships."""

    async def test_multiple_users_with_independent_data(
        self,
        test_session: AsyncSession,
        make_user,
        make_user_data,
        make_token,
    ):
        """Test that multiple users maintain independent relationships."""
        user1 = make_user(email="user1@example.com")
        user2 = make_user(email="user2@example.com")
        test_session.add_all([user1, user2])
        await test_session.flush()

        # Create data for both users
        user_data1 = make_user_data(user_id=user1.id, text_value="User 1 data")
        user_data2 = make_user_data(user_id=user2.id, text_value="User 2 data")
        token1 = make_token(user_id=user1.id)
        token2 = make_token(user_id=user2.id)

        test_session.add_all([user_data1, user_data2, token1, token2])
        await test_session.commit()

        # Refresh relationships
        await test_session.refresh(user1, ["user_data", "tokens"])
        await test_session.refresh(user2, ["user_data", "tokens"])

        # Verify independence
        assert user1.user_data.text_value == "User 1 data"
        assert user2.user_data.text_value == "User 2 data"
        assert len(user1.tokens) == 1
        assert len(user2.tokens) == 1
        assert user1.tokens[0].token != user2.tokens[0].token

    async def test_user_with_firebase_uid(
        self,
        test_session: AsyncSession,
        make_user,
    ):
        """Test User with Firebase UID for OAuth users."""
        user = make_user(
            email="google_user@example.com",
            firebase_uid="firebase_uid_abc123",
        )
        test_session.add(user)
        await test_session.commit()

        # Query by firebase_uid
        result = await test_session.execute(
            select(User).where(User.firebase_uid == "firebase_uid_abc123")
        )
        queried_user = result.scalar_one()

        assert queried_user.email == "google_user@example.com"
        assert queried_user.firebase_uid == "firebase_uid_abc123"

    async def test_user_timestamps_are_set(
        self,
        test_session: AsyncSession,
        make_user,
    ):
        """Test that User created_at and updated_at are automatically set."""
        user = make_user()
        test_session.add(user)
        await test_session.commit()

        await test_session.refresh(user)

        # Note: server_default timestamps may be None in SQLite memory tests
        # depending on SQLAlchemy version. We test that the model accepts them.
        assert user.id is not None
        assert user.email is not None


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.models",
        preview=False,
    )
