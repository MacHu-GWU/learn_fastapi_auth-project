# -*- coding: utf-8 -*-

"""
API Routers Package.

This package contains all route definitions organized by domain.
Following FastAPI's "Bigger Applications" pattern.

Structure:
- auth_routes.py: Authentication endpoints (/api/auth/*)
- user_data_routes.py: User data CRUD (/api/user-data/*)
- pages.py: HTML page redirects (/auth/*)
- health.py: Health check endpoint (/health)
"""

from fastapi import APIRouter

from .auth_routes import router as auth_router
from .user_data_routes import router as user_data_router
from .pages import router as pages_router
from .health import router as health_router

# Main API router that combines all sub-routers
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(user_data_router)
api_router.include_router(pages_router)
api_router.include_router(health_router)
