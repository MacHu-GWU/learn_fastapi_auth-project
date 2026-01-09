# -*- coding: utf-8 -*-

"""
Unit tests for refresh token module.

Tests the function interfaces of the refresh token module.
Integration tests (actual HTTP requests with token refresh) should be done manually.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from learn_fastapi_auth.refresh_token import (
    generate_refresh_token,
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    cleanup_expired_tokens,
    get_refresh_token_cookie_settings,
)


class TestGenerateRefreshToken:
    """Tests for generate_refresh_token function."""

    def test_generates_string(self):
        """Test that function returns a string."""
        token = generate_refresh_token()
        assert isinstance(token, str)

    def test_generates_correct_length(self):
        """Test that token has appropriate length (64 chars from 48 bytes)."""
        token = generate_refresh_token()
        assert len(token) == 64

    def test_generates_unique_tokens(self):
        """Test that each call generates a unique token."""
        tokens = [generate_refresh_token() for _ in range(100)]
        # All tokens should be unique
        assert len(set(tokens)) == 100

    def test_generates_url_safe_token(self):
        """Test that token is URL-safe (no special characters)."""
        token = generate_refresh_token()
        # URL-safe base64 only contains alphanumeric, - and _
        assert all(c.isalnum() or c in "-_" for c in token)


class TestCreateRefreshToken:
    """Tests for create_refresh_token function."""

    @pytest.mark.asyncio
    async def test_creates_and_stores_token(self):
        """Test that function creates a token and stores it in database."""
        mock_session = AsyncMock()
        user_id = uuid.uuid4()

        token = await create_refresh_token(mock_session, user_id)

        assert isinstance(token, str)
        assert len(token) == 64
        # Verify session.add was called with a RefreshToken
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestValidateRefreshToken:
    """Tests for validate_refresh_token function."""

    @pytest.mark.asyncio
    async def test_returns_user_id_for_valid_token(self):
        """Test that valid token returns user ID."""
        mock_session = AsyncMock()
        user_id = uuid.uuid4()

        # Create mock refresh token
        mock_token = MagicMock()
        mock_token.user_id = user_id
        mock_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_session.execute.return_value = mock_result

        result = await validate_refresh_token(mock_session, "test_token")

        assert result == user_id

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_token(self):
        """Test that nonexistent token returns None."""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await validate_refresh_token(mock_session, "nonexistent_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_expired_token(self):
        """Test that expired token returns None and is deleted."""
        mock_session = AsyncMock()
        user_id = uuid.uuid4()

        # Create mock expired token
        mock_token = MagicMock()
        mock_token.user_id = user_id
        mock_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_session.execute.return_value = mock_result

        result = await validate_refresh_token(mock_session, "expired_token")

        assert result is None
        # Verify expired token was deleted
        mock_session.delete.assert_called_once_with(mock_token)
        mock_session.commit.assert_called_once()


class TestRevokeRefreshToken:
    """Tests for revoke_refresh_token function."""

    @pytest.mark.asyncio
    async def test_revokes_existing_token(self):
        """Test that existing token is revoked and returns True."""
        mock_session = AsyncMock()
        mock_token = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_session.execute.return_value = mock_result

        result = await revoke_refresh_token(mock_session, "test_token")

        assert result is True
        mock_session.delete.assert_called_once_with(mock_token)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent_token(self):
        """Test that nonexistent token returns False."""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await revoke_refresh_token(mock_session, "nonexistent_token")

        assert result is False
        mock_session.delete.assert_not_called()


class TestRevokeAllUserRefreshTokens:
    """Tests for revoke_all_user_refresh_tokens function."""

    @pytest.mark.asyncio
    async def test_revokes_all_tokens_and_returns_count(self):
        """Test that all user tokens are revoked and count is returned."""
        mock_session = AsyncMock()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        count = await revoke_all_user_refresh_tokens(mock_session, user_id)

        assert count == 5
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestCleanupExpiredTokens:
    """Tests for cleanup_expired_tokens function."""

    @pytest.mark.asyncio
    async def test_deletes_expired_tokens_and_returns_count(self):
        """Test that expired tokens are deleted and count is returned."""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.rowcount = 10
        mock_session.execute.return_value = mock_result

        count = await cleanup_expired_tokens(mock_session)

        assert count == 10
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestGetRefreshTokenCookieSettings:
    """Tests for get_refresh_token_cookie_settings function."""

    def test_returns_dict_with_required_keys(self):
        """Test that function returns dict with all required cookie settings."""
        settings = get_refresh_token_cookie_settings()

        assert isinstance(settings, dict)
        assert "key" in settings
        assert "httponly" in settings
        assert "secure" in settings
        assert "samesite" in settings
        assert "max_age" in settings
        assert "path" in settings

    def test_httponly_is_true(self):
        """Test that httponly is True for security."""
        settings = get_refresh_token_cookie_settings()
        assert settings["httponly"] is True

    def test_path_restricts_to_auth_endpoints(self):
        """Test that cookie path is restricted to auth endpoints."""
        settings = get_refresh_token_cookie_settings()
        assert settings["path"] == "/api/auth"
