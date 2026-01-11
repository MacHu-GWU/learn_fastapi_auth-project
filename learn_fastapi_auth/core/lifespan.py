# -*- coding: utf-8 -*-

"""
Application Lifespan Management.

Handles startup and shutdown events for the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..auth.firebase import init_firebase
from ..one.api import one


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
    - Creates database tables if they don't exist
    - Initializes Firebase if enabled

    Shutdown:
    - (cleanup tasks can be added here)
    """
    # Startup
    await one.create_db_and_tables()

    # Initialize Firebase if enabled
    if one.env.firebase_enabled:
        init_firebase()

    yield

    # Shutdown (add cleanup tasks here if needed)
