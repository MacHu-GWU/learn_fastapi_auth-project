# -*- coding: utf-8 -*-

"""
Middleware Configuration.

This module centralizes all middleware setup for the FastAPI application.

See :func:`setup_all_middleware` for the complete middleware stack and execution order.
"""

import json
import os
import uuid

import jwt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware

from ..csrf import setup_csrf_protection
from ..one.api import one
from ..ratelimit import create_path_rate_limit_middleware, setup_rate_limiting
from ..refresh_token import create_refresh_token, get_refresh_token_cookie_settings


def setup_all_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.

    Middleware Stack
    ================

    - **CORS** (:func:`setup_cors`): Allow cross-origin requests from frontend
    - **Rate Limiting** (:func:`setup_slowapi_middleware`): Global rate limiting for decorated routes
    - **Path Rate Limiting** (:func:`setup_path_rate_limits`): Rate limits for fastapi-users routes
    - **CSRF Protection** (:func:`setup_csrf`): Prevent cross-site request forgery attacks
    - **Login Middleware** (:func:`setup_login_middleware`): Add refresh token cookie after login

    Execution Order (Important!)
    ============================

    Middleware follows the **onion model**: added last = executes first.

    **Code addition order** (in this function)::

        1. CORS           ← added first
        2. Rate Limiting
        3. Path Rate Limiting
        4. CSRF
        5. Login          ← added last

    **Request processing order** (reversed)::

        Request  →  CORS → RateLimit → PathLimit → CSRF → Login → Route Handler
        Response ←  CORS ← RateLimit ← PathLimit ← CSRF ← Login ← Route Handler

    Why this order?

    1. **CORS first**: Must add CORS headers even if request is rejected later
    2. **Rate limiting early**: Block abusive requests before expensive operations
    3. **CSRF before business logic**: Security check before processing
    4. **Login last**: Needs to intercept response after route handler completes
    """
    # CORS (outermost - processes first on request, last on response)
    setup_cors(app)

    # Rate limiting
    setup_slowapi_middleware(app)

    # Path-based rate limiting for fastapi-users routes
    setup_path_rate_limits(app)

    # CSRF protection
    setup_csrf(app)

    # Login middleware (innermost - processes last on request, first on response)
    setup_login_middleware(app)


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS (Cross-Origin Resource Sharing) middleware.

    Why CORS?
    =========

    Browsers block requests from different origins by default (Same-Origin Policy).
    Without CORS, your frontend (localhost:3000) cannot call your backend (localhost:8000)::

        Frontend (localhost:3000) ──request──> Backend (localhost:8000)
                                                    ↓
                                        Browser: Different port! Blocked!
                                                    ↓
                                        CORS Header: "localhost:3000 is allowed"
                                                    ↓
                                        Browser: OK, proceed

    Configuration
    =============

    Allowed origins:

    - ``localhost:3000``, ``127.0.0.1:3000`` - Next.js dev server
    - ``*.vercel.app`` - Vercel deployments (when VERCEL env is set)
    - Custom origins from ``CORS_ORIGINS`` environment variable

    Important settings:

    - ``allow_credentials=True`` - Required for cookies (refresh token)
    - ``allow_methods=["*"]`` - Allow all HTTP methods
    - ``allow_headers=["*"]`` - Allow all headers (including Authorization)
    """
    cors_origins = [
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ]

    # Add production origins
    if os.environ.get("VERCEL"):
        cors_origins.extend(
            [
                "https://learn-fastapi-auth-project.vercel.app",
                "https://*.vercel.app",  # Preview deployments
            ]
        )

    # Allow additional origins from environment variable
    extra_origins = os.environ.get("CORS_ORIGINS", "")
    if extra_origins:
        cors_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,  # Allow cookies for refresh token
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_slowapi_middleware(app: FastAPI) -> None:
    """
    Configure SlowAPI rate limiting middleware.

    Why Two Steps?
    ==============

    SlowAPI requires two separate setup steps:

    1. **Register limiter** (:func:`setup_rate_limiting`): Stores the limiter instance
       in ``app.state.limiter`` so ``@limiter.limit()`` decorators can find it.

    2. **Add middleware** (this function): Adds the actual middleware that intercepts
       requests and enforces rate limits.

    This function handles both steps together for convenience.

    How It Works
    ============

    ::

        @router.get("/api/resource")
        @limiter.limit("10/minute")      ← Decorator marks the route
        async def get_resource():
            ...

        Request arrives
              ↓
        SlowAPIMiddleware checks if route has @limiter.limit
              ↓
        Yes → Check rate limit for client IP
              ↓
        Under limit? → Continue
        Over limit?  → Return 429 Too Many Requests
    """
    setup_rate_limiting(app)
    app.add_middleware(SlowAPIMiddleware)


def setup_path_rate_limits(app: FastAPI) -> None:
    """
    Configure path-based rate limiting for specific routes.

    Why Path-Based Rate Limiting?
    =============================

    The ``@limiter.limit()`` decorator only works on routes we define ourselves.
    Routes from ``fastapi-users`` (login, register, etc.) are pre-built and cannot
    be decorated directly.

    This middleware intercepts requests by path and applies rate limits::

        POST /api/auth/login
                ↓
        Middleware: Check if path matches "/api/auth/login"
                ↓
        Yes → Apply "5/minute" rate limit
                ↓
        Under limit? → Continue to route handler
        Over limit?  → Return 429 Too Many Requests

    Rate Limits
    ===========

    +---------------------------+-------------+--------------------------------+
    | Path                      | Limit       | Reason                         |
    +===========================+=============+================================+
    | ``/api/auth/login``       | 5/minute    | Prevent brute-force attacks    |
    +---------------------------+-------------+--------------------------------+
    | ``/api/auth/register``    | 10/hour     | Prevent spam account creation  |
    +---------------------------+-------------+--------------------------------+
    | ``/api/auth/forgot-password`` | 3/hour  | Prevent email bombing          |
    +---------------------------+-------------+--------------------------------+
    """
    path_rate_limits = {
        "/api/auth/login": one.env.rate_limit_login,
        "/api/auth/register": one.env.rate_limit_register,
        "/api/auth/forgot-password": one.env.rate_limit_forgot_password,
    }
    app.middleware("http")(create_path_rate_limit_middleware(path_rate_limits))


def setup_csrf(app: FastAPI) -> None:
    """
    Configure CSRF (Cross-Site Request Forgery) protection middleware.

    Why CSRF Protection?
    ====================

    CSRF attacks exploit the browser's automatic cookie sending behavior::

        1. User logs into your-app.com (session cookie set)
        2. User visits malicious-site.com
        3. Malicious site has: <form action="your-app.com/transfer" method="POST">
        4. Form auto-submits, browser sends cookies automatically
        5. Your backend thinks it's a legitimate request ← Danger!

    How CSRF Protection Works
    =========================

    ::

        1. Backend generates CSRF token, sends to frontend
        2. Frontend includes token in request header (X-CSRF-Token)
        3. Backend validates token matches
        4. Malicious sites can't access the token (Same-Origin Policy)

    Configuration
    =============

    The CSRF secret key is derived from the application's ``SECRET_KEY``.

    Protected methods: POST, PUT, PATCH, DELETE (state-changing operations).
    """
    setup_csrf_protection(app, one.env.secret_key)


def setup_login_middleware(app: FastAPI) -> None:
    """
    Configure login middleware for refresh token handling.

    This middleware intercepts login responses to add refresh token cookies.
    See :func:`_add_refresh_token_on_login` for implementation details.
    """
    app.middleware("http")(_add_refresh_token_on_login)


async def _add_refresh_token_on_login(request: Request, call_next):
    """
    Middleware to add refresh token cookie after successful login.

    Why This Middleware?
    ====================

    The ``fastapi-users`` login route only returns an access token.
    We need to also issue a refresh token for the token refresh mechanism.

    Since we can't modify ``fastapi-users`` route directly, this middleware
    intercepts the login response and adds the refresh token cookie.

    How It Works
    ============

    ::

        POST /api/auth/login {username, password, remember_me}
                ↓
        [1] Middleware intercepts request, extracts remember_me parameter
                ↓
        [2] Request passes through to fastapi-users login handler
                ↓
        [3] Login handler returns {access_token: "..."}
                ↓
        [4] Middleware intercepts response
                ↓
        [5] Decode access_token to get user_id (no signature verification needed)
                ↓
        [6] Create refresh_token in database
                ↓
        [7] Set refresh_token as HttpOnly cookie
                ↓
        [8] Return modified response with cookie

    Remember Me Feature
    ===================

    The ``remember_me`` form field controls refresh token lifetime:

    - ``remember_me=true``: 30 days (configured via ``remember_me_refresh_token_lifetime``)
    - ``remember_me=false`` (default): 7 days (configured via ``refresh_token_lifetime``)

    Technical Notes
    ===============

    - Request body is read and cached to extract ``remember_me``, then re-attached
      so the route handler can read it again
    - Response body is consumed to parse JSON, then a new JSONResponse is created
    - JWT is decoded without signature verification (we trust our own response)
    """
    # Check if this is a login request and extract remember_me before processing
    remember_me = False
    if request.url.path == "/api/auth/login" and request.method == "POST":
        # Read and cache request body to extract remember_me
        body_bytes = await request.body()

        # Parse form data to get remember_me parameter
        try:
            from urllib.parse import parse_qs

            form_data = parse_qs(body_bytes.decode())
            remember_me_values = form_data.get("remember_me", ["false"])
            remember_me = remember_me_values[0].lower() == "true"
        except Exception:
            pass

        # Store the body in request state so it can be re-read by the route
        # We need to replace the receive to allow body to be read again
        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request = Request(request.scope, receive, request._send)

    response = await call_next(request)

    # Only process POST to login endpoint with successful response
    if (
        request.url.path == "/api/auth/login"
        and request.method == "POST"
        and response.status_code == 200
    ):
        # Read the response body to get the access token
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            # Parse the JSON response to get access_token
            data = json.loads(body.decode())
            access_token = data.get("access_token")

            if access_token:
                # Decode JWT to get user_id (without verification since we trust it)
                payload = jwt.decode(access_token, options={"verify_signature": False})
                user_id = payload.get("sub")

                if user_id:
                    # Determine token lifetime based on remember_me
                    token_lifetime = (
                        one.env.remember_me_refresh_token_lifetime
                        if remember_me
                        else one.env.refresh_token_lifetime
                    )

                    async with one.async_session_maker() as session:
                        refresh_token_str = await create_refresh_token(
                            session, uuid.UUID(user_id), token_lifetime
                        )

                    # Create new response with refresh token cookie
                    new_response = JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                    cookie_settings = get_refresh_token_cookie_settings(token_lifetime)
                    new_response.set_cookie(
                        value=refresh_token_str,
                        **cookie_settings,
                    )
                    return new_response
        except Exception:
            # If anything fails, return original response
            pass

        # Return response with original body
        return JSONResponse(
            content=json.loads(body.decode()) if body else {},
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    return response
