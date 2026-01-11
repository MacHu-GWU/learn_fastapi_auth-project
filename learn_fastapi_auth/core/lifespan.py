# -*- coding: utf-8 -*-

"""
Application Lifespan Management.

This module manages the `FastAPI application lifecycle <https://fastapi.tiangolo.com/advanced/events/>`_ using an async context manager.

What is Lifespan?
=================
Lifespan handles **application-level** resource management:

- **Startup**: Initialize resources before the first request
- **Shutdown**: Clean up resources after the last request

These resources are shared across all requests during the application's lifetime.

Why Context Manager (not just a startup hook)?
==============================================

A context manager naturally handles the full resource lifecycle::

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # === STARTUP ===
        db_pool = create_connection_pool()
        redis = await aioredis.create_pool()

        yield  # <-- Application runs here, handles requests

        # === SHUTDOWN ===
        # Variables from startup are still accessible!
        await db_pool.close()
        await redis.close()

If we only had a startup hook, we'd need global variables to access
resources during shutdown. Context manager solves this elegantly.

Typical Lifespan Resources
==========================

+---------------------+------------------------+------------------------+
| Resource            | Startup                | Shutdown               |
+=====================+========================+========================+
| Database pool       | Create connection pool | Close all connections  |
+---------------------+------------------------+------------------------+
| Redis connection    | Connect to Redis       | Disconnect             |
+---------------------+------------------------+------------------------+
| ML model            | Load into memory       | Release memory         |
+---------------------+------------------------+------------------------+
| Background workers  | Start worker threads   | Wait for completion    |
+---------------------+------------------------+------------------------+
| Firebase SDK        | Initialize SDK         | (no cleanup needed)    |
+---------------------+------------------------+------------------------+

Old Way vs New Way
==================

The old ``@app.on_event("startup")`` decorator is deprecated::

    # ❌ Deprecated - startup and shutdown are separate, can't share variables
    @app.on_event("startup")
    async def startup():
        app.state.db = create_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await app.state.db.close()

    # ✅ Recommended - lifespan context manager
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = create_pool()
        yield
        await db.close()

Usage
=====

Pass the lifespan function to FastAPI::

    app = FastAPI(lifespan=lifespan)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..one.api import one


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    This function is called once when the application starts and provides
    a context that lives until the application shuts down.

    Startup (before yield):
        - Creates database tables if they don't exist
        - Initializes Firebase Admin SDK if enabled

    Shutdown (after yield):
        - Add cleanup tasks here when needed (e.g., close connection pools)

    Args:
        app: The FastAPI application instance.
            Can be used to store state via ``app.state`` if needed.

    Yields:
        Control to the application. All requests are handled while yielded.

    Example of adding shutdown cleanup::

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await one.create_db_and_tables()
            one.init_firebase()

            yield

            # Cleanup on shutdown
            await one.async_engine.dispose()
            logger.info("Database connections closed")
    """
    # =========================================================================
    # Startup
    # =========================================================================
    await one.create_db_and_tables()
    one.init_firebase()

    yield

    # =========================================================================
    # Shutdown
    # =========================================================================
    # Add cleanup tasks here if needed, for example:
    # await one.async_engine.dispose()
