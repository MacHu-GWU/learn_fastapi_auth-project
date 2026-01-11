# -*- coding: utf-8 -*-

"""
FastAPI Application Entry Point.

This module provides the FastAPI application instance.
All configuration is handled by the core.app_factory module.
"""

from .core import create_app

# Create the application instance
app = create_app()
