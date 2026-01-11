# -*- coding: utf-8 -*-

"""
FastAPI Application Factory.

Creates and configures the FastAPI application with all routes,
middleware, and extensions.
"""

from fastapi import FastAPI

from ..admin import setup_admin
from ..routers import api_router
from .lifespan import lifespan
from .middleware import setup_all_middleware


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function:
    1. Creates the FastAPI app with metadata
    2. Configures all middleware (CORS, rate limiting, CSRF, login)
    3. Includes all API routers
    4. Sets up the admin dashboard

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="FastAPI User Authentication",
        description="A SaaS authentication service with email verification",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Setup all middleware
    setup_all_middleware(app)

    # Include all routers
    app.include_router(api_router)

    # Setup admin dashboard
    setup_admin(app)

    return app
