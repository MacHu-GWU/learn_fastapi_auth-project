# -*- coding: utf-8 -*-

"""
Core Application Package.

Contains core application configuration:
- app_factory.py: FastAPI application factory
- middleware.py: Middleware configuration
- lifespan.py: Application lifespan management
"""

from .app_factory import create_app

__all__ = ["create_app"]
