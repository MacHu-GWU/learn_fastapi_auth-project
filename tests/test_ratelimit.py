# -*- coding: utf-8 -*-

"""
Unit tests for rate limiting functionality.

Tests cover:
- get_client_ip function
- check_path_rate_limit function
- rate limit exceeded responses
- middleware path matching
"""

from unittest.mock import MagicMock

import pytest
from starlette.datastructures import Headers

from learn_fastapi_auth.ratelimit import (
    PathRateLimitExceeded,
    check_path_rate_limit,
    get_client_ip,
    reset_rate_limit_storage,
)


class MockRequest:
    """Mock request object for testing."""

    def __init__(self, headers: dict = None, client_host: str = "127.0.0.1"):
        self.headers = Headers(headers or {})
        self.client = MagicMock()
        self.client.host = client_host


class TestGetClientIP:
    """Test get_client_ip function."""

    def test_direct_connection(self):
        """Test getting IP from direct connection."""
        request = MockRequest(client_host="192.168.1.100")
        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_with_x_forwarded_for_single(self):
        """Test getting IP from X-Forwarded-For header (single IP)."""
        request = MockRequest(
            headers={"X-Forwarded-For": "10.0.0.1"},
            client_host="192.168.1.100",
        )
        ip = get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_with_x_forwarded_for_multiple(self):
        """Test getting IP from X-Forwarded-For header (multiple IPs)."""
        request = MockRequest(
            headers={"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"},
            client_host="192.168.1.100",
        )
        ip = get_client_ip(request)
        # Should return the first (original client) IP
        assert ip == "203.0.113.195"

    def test_with_x_forwarded_for_with_spaces(self):
        """Test getting IP from X-Forwarded-For with extra spaces."""
        request = MockRequest(
            headers={"X-Forwarded-For": "  10.0.0.1  ,  proxy1  "},
            client_host="192.168.1.100",
        )
        ip = get_client_ip(request)
        # Should strip whitespace
        assert ip == "10.0.0.1"


class TestCheckPathRateLimit:
    """Test check_path_rate_limit function."""

    def setup_method(self):
        """Reset rate limit storage before each test."""
        reset_rate_limit_storage()

    def test_within_limit(self):
        """Test requests within rate limit pass."""
        request = MockRequest(client_host="10.0.0.1")

        # Should not raise for first few requests
        for _ in range(3):
            result = check_path_rate_limit(request, "5/minute", "/api/test")
            assert result is True

    def test_exceeds_limit(self):
        """Test requests exceeding rate limit raise exception."""
        request = MockRequest(client_host="10.0.0.2")

        # Make requests up to the limit
        for _ in range(5):
            check_path_rate_limit(request, "5/minute", "/api/test")

        # Next request should exceed limit
        with pytest.raises(PathRateLimitExceeded) as exc_info:
            check_path_rate_limit(request, "5/minute", "/api/test")

        assert exc_info.value.limit_string == "5/minute"

    def test_different_ips_have_separate_limits(self):
        """Test that different IPs have separate rate limit counters."""
        request1 = MockRequest(client_host="10.0.0.3")
        request2 = MockRequest(client_host="10.0.0.4")

        # Exhaust limit for request1
        for _ in range(5):
            check_path_rate_limit(request1, "5/minute", "/api/test")

        # request1 should now be blocked
        with pytest.raises(PathRateLimitExceeded):
            check_path_rate_limit(request1, "5/minute", "/api/test")

        # request2 should still work (different IP)
        result = check_path_rate_limit(request2, "5/minute", "/api/test")
        assert result is True

    def test_different_paths_have_separate_limits(self):
        """Test that different paths have separate rate limit counters."""
        request = MockRequest(client_host="10.0.0.5")

        # Exhaust limit for /api/login
        for _ in range(5):
            check_path_rate_limit(request, "5/minute", "/api/login")

        # /api/login should now be blocked
        with pytest.raises(PathRateLimitExceeded):
            check_path_rate_limit(request, "5/minute", "/api/login")

        # /api/register should still work (different path)
        result = check_path_rate_limit(request, "5/minute", "/api/register")
        assert result is True


class TestPathRateLimitExceeded:
    """Test PathRateLimitExceeded exception."""

    def test_exception_message(self):
        """Test exception contains limit string."""
        exc = PathRateLimitExceeded("10/hour")
        assert exc.limit_string == "10/hour"
        assert "10/hour" in str(exc)

    def test_exception_is_catchable(self):
        """Test exception can be caught."""
        try:
            raise PathRateLimitExceeded("5/minute")
        except PathRateLimitExceeded as e:
            assert e.limit_string == "5/minute"
        except Exception:
            pytest.fail("Should have caught PathRateLimitExceeded")


class TestResetRateLimitStorage:
    """Test reset_rate_limit_storage function."""

    def test_reset_clears_counters(self):
        """Test that reset clears all rate limit counters."""
        request = MockRequest(client_host="10.0.0.6")

        # Exhaust limit
        for _ in range(5):
            check_path_rate_limit(request, "5/minute", "/api/test")

        # Should be blocked
        with pytest.raises(PathRateLimitExceeded):
            check_path_rate_limit(request, "5/minute", "/api/test")

        # Reset storage
        reset_rate_limit_storage()

        # Should work again
        result = check_path_rate_limit(request, "5/minute", "/api/test")
        assert result is True


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.ratelimit",
        preview=False,
    )
