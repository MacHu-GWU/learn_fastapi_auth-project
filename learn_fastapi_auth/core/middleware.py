# -*- coding: utf-8 -*-

"""
Middleware Configuration.

Centralizes all middleware setup for the FastAPI application:
- CORS middleware
- Rate limiting middleware
- CSRF protection middleware
- Login middleware (refresh token handling)
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


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.

    Allows requests from:
    - localhost:3000 (Next.js dev server)
    - Vercel production domain
    - Custom origins from CORS_ORIGINS env var
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


def setup_path_rate_limits(app: FastAPI) -> None:
    """
    Configure path-based rate limiting for fastapi-users routes.

    These routes cannot use @limiter.limit() decorator directly,
    so we use middleware-based rate limiting.
    """
    path_rate_limits = {
        "/api/auth/login": one.env.rate_limit_login,  # Login: 5/minute
        "/api/auth/register": one.env.rate_limit_register,  # Register: 10/hour
        "/api/auth/forgot-password": one.env.rate_limit_forgot_password,  # Reset: 3/hour
    }
    app.middleware("http")(create_path_rate_limit_middleware(path_rate_limits))


async def add_refresh_token_on_login(request: Request, call_next):
    """
    Middleware to add refresh token cookie after successful login.

    This intercepts responses from /api/auth/login and adds a refresh token
    cookie for the token refresh mechanism.

    Supports "Remember Me" functionality:
    - If remember_me=true: refresh token lasts 30 days
    - If remember_me=false (default): refresh token lasts 7 days
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


def setup_all_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.

    Order matters! Middleware is executed in reverse order of addition.
    The last middleware added is the first to process requests.

    Current order (request flow):
    1. Login middleware (adds refresh token cookie)
    2. CSRF protection
    3. Path-based rate limiting
    4. SlowAPI rate limiting
    5. CORS
    """
    # CORS (outermost - processes first on request, last on response)
    setup_cors(app)

    # Rate limiting
    setup_rate_limiting(app)
    app.add_middleware(SlowAPIMiddleware)

    # Path-based rate limiting for fastapi-users routes
    setup_path_rate_limits(app)

    # CSRF protection
    setup_csrf_protection(app, one.env.secret_key)

    # Login middleware (innermost - processes last on request, first on response)
    app.middleware("http")(add_refresh_token_on_login)
