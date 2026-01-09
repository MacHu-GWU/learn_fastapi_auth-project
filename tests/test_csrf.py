# -*- coding: utf-8 -*-

"""
Unit tests for CSRF protection module.

Tests the function interfaces of the CSRF protection module.
Integration tests (actual HTTP requests with CSRF validation) should be done manually.
"""

import re
from unittest.mock import MagicMock

import pytest

from learn_fastapi_auth.csrf import (
    create_csrf_exempt_patterns,
    create_csrf_required_patterns,
    get_csrf_cookie_name,
    get_csrf_header_name,
    get_csrf_token,
)


class TestGetCSRFToken:
    """Tests for get_csrf_token function."""

    def test_returns_token_when_present(self):
        """Test that CSRF token is returned when present in cookies."""
        mock_request = MagicMock()
        mock_request.cookies = {"csrftoken": "test-token-123"}

        result = get_csrf_token(mock_request)

        assert result == "test-token-123"

    def test_returns_none_when_missing(self):
        """Test that None is returned when CSRF token is not in cookies."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        result = get_csrf_token(mock_request)

        assert result is None

    def test_returns_none_with_different_cookie(self):
        """Test that None is returned when a different cookie exists."""
        mock_request = MagicMock()
        mock_request.cookies = {"other_cookie": "some-value"}

        result = get_csrf_token(mock_request)

        assert result is None


class TestCreateCSRFExemptPatterns:
    """Tests for create_csrf_exempt_patterns function."""

    def test_returns_list_of_patterns(self):
        """Test that function returns a list of compiled regex patterns."""
        patterns = create_csrf_exempt_patterns()

        assert isinstance(patterns, list)
        assert len(patterns) > 0
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)

    def test_api_routes_are_exempt(self):
        """Test that /api/* routes are marked as exempt."""
        patterns = create_csrf_exempt_patterns()

        test_urls = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/users/me",
            "/api/user-data",
        ]

        for url in test_urls:
            matches = any(p.match(url) for p in patterns)
            assert matches, f"Expected {url} to be exempt"

    def test_health_endpoint_is_exempt(self):
        """Test that /health endpoint is marked as exempt."""
        patterns = create_csrf_exempt_patterns()

        matches = any(p.match("/health") for p in patterns)
        assert matches

    def test_static_files_are_exempt(self):
        """Test that /static/* routes are marked as exempt."""
        patterns = create_csrf_exempt_patterns()

        test_urls = [
            "/static/css/style.css",
            "/static/js/app.js",
            "/static/images/logo.png",
        ]

        for url in test_urls:
            matches = any(p.match(url) for p in patterns)
            assert matches, f"Expected {url} to be exempt"

    def test_docs_endpoints_are_exempt(self):
        """Test that API documentation endpoints are marked as exempt."""
        patterns = create_csrf_exempt_patterns()

        test_urls = [
            "/docs",
            "/docs/",
            "/redoc",
            "/redoc/",
            "/openapi.json",
        ]

        for url in test_urls:
            matches = any(p.match(url) for p in patterns)
            assert matches, f"Expected {url} to be exempt"

    def test_page_routes_are_not_exempt(self):
        """Test that HTML page routes are NOT marked as exempt."""
        patterns = create_csrf_exempt_patterns()

        test_urls = [
            "/signin",
            "/signup",
            "/app",
            "/forgot-password",
        ]

        for url in test_urls:
            matches = any(p.match(url) for p in patterns)
            assert not matches, f"Expected {url} to NOT be exempt"


class TestCreateCSRFRequiredPatterns:
    """Tests for create_csrf_required_patterns function."""

    def test_returns_none_for_all_protection(self):
        """Test that function returns None to protect all non-exempt URLs."""
        result = create_csrf_required_patterns()

        assert result is None


class TestGetCSRFHeaderName:
    """Tests for get_csrf_header_name function."""

    def test_returns_correct_header_name(self):
        """Test that function returns the correct CSRF header name."""
        result = get_csrf_header_name()

        assert result == "x-csrftoken"


class TestGetCSRFCookieName:
    """Tests for get_csrf_cookie_name function."""

    def test_returns_cookie_name_from_config(self):
        """Test that function returns the cookie name from configuration."""
        result = get_csrf_cookie_name()

        # Default value from config
        assert result == "csrftoken"
