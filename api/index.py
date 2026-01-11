# -*- coding: utf-8 -*-

"""
Vercel serverless function entry point for FastAPI.

This file is required by Vercel to expose the FastAPI app as a serverless function.
All /api/* routes will be handled by this handler.
"""

from learn_fastapi_auth.app import app

# Vercel expects 'app' as the ASGI application
# Do not use 'handler' - that's for WSGI/HTTP handlers
