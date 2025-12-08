# -*- coding: utf-8 -*-

"""
Unit tests for application endpoints.

Tests cover:
- Health check endpoint
- Root endpoint
"""

from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRoot:
    """Test root endpoint."""

    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns welcome message."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]


if __name__ == "__main__":
    from learn_fastapi_auth.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_fastapi_auth.app",
        preview=False,
    )
