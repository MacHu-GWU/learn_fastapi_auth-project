# -*- coding: utf-8 -*-

"""
Unit tests for learn_fastapi_auth.auth.users module.

Tests cover direct function calls (parameter in, parameter out):
- get_jwt_strategy()
- store_token()
- delete_token()
- validate_token_in_db()
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.auth.users import (
    delete_token,
    get_jwt_strategy,
    store_token,
    validate_token_in_db,
)
from learn_fastapi_auth.models import Token


class TestJWTStrategy:
    """Test JWT strategy configuration."""

    def test_get_jwt_strategy(self):
        """Test JWT strategy returns correct configuration."""
        strategy = get_jwt_strategy()
        assert strategy is not None
        assert strategy.lifetime_seconds > 0


class TestTokenManagement:
    """Test token database management functions."""

    async def test_store_token(
        self,
        test_session: AsyncSession,
    ):
        """Test storing a token in database."""
        user_id = uuid.uuid4()
        token_str = f"test_token_{uuid.uuid4().hex}"

        token = await store_token(test_session, token_str, user_id)

        assert token.token == token_str
        assert token.user_id == user_id
        assert token.expires_at > datetime.now(timezone.utc)

    async def test_validate_token_in_db_valid(
        self,
        test_session: AsyncSession,
    ):
        """Test validating a valid token."""
        user_id = uuid.uuid4()
        token_str = f"valid_token_{uuid.uuid4().hex}"

        await store_token(test_session, token_str, user_id)
        is_valid = await validate_token_in_db(test_session, token_str)

        assert is_valid is True

    async def test_validate_token_in_db_not_found(
        self,
        test_session: AsyncSession,
    ):
        """Test validating a non-existent token."""
        is_valid = await validate_token_in_db(test_session, "non_existent_token")
        assert is_valid is False

    async def test_validate_token_in_db_expired(
        self,
        test_session: AsyncSession,
    ):
        """Test validating an expired token."""
        user_id = uuid.uuid4()
        token_str = f"expired_token_{uuid.uuid4().hex}"

        # Manually create expired token
        expired_token = Token(
            token=token_str,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        test_session.add(expired_token)
        await test_session.commit()

        is_valid = await validate_token_in_db(test_session, token_str)
        assert is_valid is False

    async def test_delete_token_success(
        self,
        test_session: AsyncSession,
    ):
        """Test deleting an existing token."""
        user_id = uuid.uuid4()
        token_str = f"delete_token_{uuid.uuid4().hex}"

        await store_token(test_session, token_str, user_id)
        result = await delete_token(test_session, token_str)

        assert result is True

        # Verify token is deleted
        query_result = await test_session.execute(
            select(Token).where(Token.token == token_str)
        )
        assert query_result.scalar_one_or_none() is None

    async def test_delete_token_not_found(
        self,
        test_session: AsyncSession,
    ):
        """Test deleting a non-existent token."""
        result = await delete_token(test_session, "non_existent_token")
        assert result is False


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.auth.users",
        preview=False,
    )
