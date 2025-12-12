# -*- coding: utf-8 -*-

"""
Rate Limiting Module.

Provides request rate limiting functionality using slowapi library.
This helps protect the application from brute force attacks, DDoS,
and API abuse.

Rate limit format: "<count>/<period>"
- count: maximum number of requests allowed
- period: time period (second, minute, hour, day)

Example values:
- "5/minute": 5 requests per minute
- "10/hour": 10 requests per hour
- "100/day": 100 requests per day
"""

from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from limits import parse
from limits.storage import MemoryStorage
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


class PathRateLimitExceeded(Exception):
    """Exception raised when path-based rate limit is exceeded."""

    def __init__(self, limit_string: str):
        self.limit_string = limit_string
        super().__init__(f"Rate limit exceeded: {limit_string}")


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    This function handles both direct connections and proxied requests.
    It checks X-Forwarded-For header first (for reverse proxy setups),
    then falls back to the remote address.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Check for X-Forwarded-For header (set by reverse proxies like nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first one is the original client IP
        return forwarded_for.split(",")[0].strip()

    # Fall back to the direct remote address
    return get_remote_address(request)


# Create the limiter instance with custom key function
limiter = Limiter(key_func=get_client_ip)

# Storage for path-based rate limiting (used for fastapi-users routes)
_path_storage = MemoryStorage()


def reset_rate_limit_storage():
    """
    Reset the rate limit storage.

    This function clears all rate limit counters. It's primarily used
    for testing purposes to ensure tests don't affect each other.
    """
    global _path_storage
    _path_storage = MemoryStorage()


def check_path_rate_limit(
    request: Request,
    limit_string: str,
    path_identifier: str,
) -> bool:
    """
    Check rate limit for a specific path.

    This function is used for rate limiting fastapi-users routes
    that cannot use the @limiter.limit() decorator directly.

    Args:
        request: FastAPI request object
        limit_string: Rate limit in format like "5/minute"
        path_identifier: Identifier for the path (e.g., "login", "register")

    Returns:
        True if request is within rate limit, False if exceeded

    Raises:
        PathRateLimitExceeded: When rate limit is exceeded
    """
    client_ip = get_client_ip(request)
    # Create a unique key combining client IP and path
    key = f"{path_identifier}:{client_ip}"

    # Parse the limit string
    rate_limit = parse(limit_string)

    # Try to acquire an entry - returns True if within limit, False if exceeded
    # acquire_entry(key, limit_amount, expiry_seconds)
    if not _path_storage.acquire_entry(key, rate_limit.amount, rate_limit.get_expiry()):
        raise PathRateLimitExceeded(limit_string)

    return True


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors from slowapi decorator.

    Returns a user-friendly JSON response with:
    - HTTP 429 status code (Too Many Requests)
    - Error message explaining the rate limit
    - Retry-After header indicating when to retry

    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception with rate limit details

    Returns:
        JSONResponse with 429 status and error details
    """
    # For slowapi RateLimitExceeded, the detail is available via the limit object
    detail = str(exc.detail) if hasattr(exc, "detail") else "Rate limit exceeded"

    response = JSONResponse(
        status_code=429,
        content={
            "detail": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. {detail}",
        },
    )

    # Add Retry-After header if available
    retry_after = getattr(exc, "retry_after", None)
    if retry_after:
        response.headers["Retry-After"] = str(retry_after)

    return response


async def path_rate_limit_exceeded_handler(
    request: Request,
    exc: PathRateLimitExceeded,
) -> JSONResponse:
    """
    Custom handler for path-based rate limit exceeded errors.

    Args:
        request: FastAPI request object
        exc: PathRateLimitExceeded exception with limit details

    Returns:
        JSONResponse with 429 status and error details
    """
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. Limit: {exc.limit_string}",
        },
    )
    return response


def create_path_rate_limit_middleware(
    path_limits: dict[str, str],
) -> Callable:
    """
    Create middleware for path-based rate limiting.

    This middleware checks requests against configured rate limits
    for specific paths, particularly useful for fastapi-users routes.

    Args:
        path_limits: Dictionary mapping path prefixes to rate limit strings
                    Example: {"/api/auth/login": "5/minute"}

    Returns:
        Middleware callable
    """

    async def middleware(request: Request, call_next):
        """Apply rate limiting based on request path."""
        path = request.url.path

        # Check if this path matches any rate limit rules
        for path_prefix, limit_string in path_limits.items():
            if path.startswith(path_prefix):
                try:
                    check_path_rate_limit(request, limit_string, path_prefix)
                except PathRateLimitExceeded as exc:
                    return await path_rate_limit_exceeded_handler(request, exc)
                break

        return await call_next(request)

    return middleware


def setup_rate_limiting(app):
    """
    Configure rate limiting for a FastAPI application.

    This function:
    1. Adds the limiter as a state attribute to the app
    2. Registers the custom rate limit exceeded handler

    Args:
        app: FastAPI application instance

    Usage:
        from learn_fastapi_auth.ratelimit import setup_rate_limiting
        app = FastAPI()
        setup_rate_limiting(app)
    """
    # Store limiter in app state so it can be accessed by decorators
    app.state.limiter = limiter

    # Register custom exception handler for rate limit errors (from @limiter.limit decorator)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Register handler for path-based rate limit errors
    app.add_exception_handler(PathRateLimitExceeded, path_rate_limit_exceeded_handler)
