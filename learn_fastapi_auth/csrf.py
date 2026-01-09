# -*- coding: utf-8 -*-

"""
CSRF Protection Module.

Provides Cross-Site Request Forgery (CSRF) protection using starlette-csrf.
CSRF attacks trick users into performing unwanted actions on authenticated sites.

How CSRF Protection Works:
1. Server generates a random CSRF token and sets it in a cookie
2. For state-changing requests (POST, PUT, DELETE), the client must:
   - Include the token in a header (X-CSRFToken) or form field
3. Server validates that the token in the request matches the cookie
4. Malicious sites cannot read the cookie due to same-origin policy

Important Notes:
- Our app uses JWT Bearer tokens stored in localStorage (not cookies)
- This means CSRF risk is already low for API endpoints
- However, HTML form submissions still benefit from CSRF protection
- API endpoints using Bearer token authentication are exempt
"""

import re
from typing import List, Optional, Set

from fastapi import Request
from starlette_csrf import CSRFMiddleware

from .config import config


def get_csrf_token(request: Request) -> Optional[str]:
    """
    Get CSRF token from request cookies.

    This function can be used in Jinja2 templates to include the
    CSRF token in forms.

    Args:
        request: FastAPI request object

    Returns:
        CSRF token string if present in cookies, None otherwise

    Usage in template:
        <input type="hidden" name="csrftoken" value="{{ csrf_token }}">
    """
    return request.cookies.get(config.csrf_cookie_name)


def create_csrf_exempt_patterns() -> List[re.Pattern]:
    """
    Create regex patterns for URLs that should be exempt from CSRF protection.

    Exempt URLs include:
    - API endpoints that use Bearer token authentication (already protected)
    - Health check endpoint
    - Static files
    - API documentation endpoints

    Returns:
        List of compiled regex patterns
    """
    exempt_patterns = [
        # API endpoints using Bearer token auth are already protected
        # against CSRF because the token is in Authorization header, not cookie
        re.compile(r"^/api/.*"),
        # Health check doesn't need CSRF
        re.compile(r"^/health$"),
        # Static files don't need CSRF
        re.compile(r"^/static/.*"),
        # API docs don't need CSRF (GET requests)
        re.compile(r"^/docs.*"),
        re.compile(r"^/redoc.*"),
        re.compile(r"^/openapi\.json$"),
        # Admin dashboard uses its own session-based authentication
        re.compile(r"^/admin.*"),
    ]
    return exempt_patterns


def create_csrf_required_patterns() -> Optional[List[re.Pattern]]:
    """
    Create regex patterns for URLs that require CSRF protection.

    If this returns None, all URLs (except exempt ones) require protection.
    If this returns a list, only matching URLs require protection.

    For our app, we return None to protect all non-exempt POST/PUT/DELETE requests.

    Returns:
        None (all non-exempt URLs require protection) or list of patterns
    """
    # Return None to protect all non-exempt URLs
    # Alternatively, you could specify specific URLs:
    # return [
    #     re.compile(r"^/auth/.*"),  # Auth form submissions
    # ]
    return None


def setup_csrf_protection(app, secret: str) -> None:
    """
    Configure CSRF protection for a FastAPI application.

    This adds the CSRFMiddleware with appropriate configuration.
    The middleware will:
    - Set a CSRF cookie on responses
    - Validate CSRF token on state-changing requests (POST, PUT, DELETE, PATCH)
    - Skip validation for safe methods (GET, HEAD, OPTIONS, TRACE)
    - Skip validation for exempt URLs

    Args:
        app: FastAPI application instance
        secret: Secret key for signing CSRF tokens (should be same as app secret)

    Usage:
        from learn_fastapi_auth.csrf import setup_csrf_protection
        app = FastAPI()
        setup_csrf_protection(app, config.secret_key)
    """
    app.add_middleware(
        CSRFMiddleware,
        secret=secret,
        exempt_urls=create_csrf_exempt_patterns(),
        required_urls=create_csrf_required_patterns(),
        cookie_name=config.csrf_cookie_name,
        cookie_secure=config.csrf_cookie_secure,
        cookie_samesite=config.csrf_cookie_samesite,
        # cookie_httponly=False allows JavaScript to read the token
        # This is necessary for AJAX requests to include the token in headers
        cookie_httponly=False,
        header_name="x-csrftoken",
    )


def get_csrf_header_name() -> str:
    """
    Get the header name for CSRF token.

    This is the header name that should be used when making AJAX requests.

    Returns:
        Header name string (x-csrftoken)

    Usage in JavaScript:
        fetch('/some-endpoint', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
    """
    return "x-csrftoken"


def get_csrf_cookie_name() -> str:
    """
    Get the cookie name for CSRF token.

    Returns:
        Cookie name string from configuration
    """
    return config.csrf_cookie_name
