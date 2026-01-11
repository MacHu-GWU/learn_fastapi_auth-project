# -*- coding: utf-8 -*-

"""
"""

import typing as T
from functools import cached_property

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..database import Base


if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneDbMixin:  # pragma: no cover
    """ """

    @cached_property
    def async_engine(self: "One"):
        """
        Create async engine
        """
        return create_async_engine(self.env.async_db_url, echo=False)

    @cached_property
    def sync_engine(self: "One"):
        """
        Create sync engine
        """
        return sa.create_engine(self.env.sync_db_url, echo=False)

    @cached_property
    def async_session_maker(self: "One"):
        """
        Create async session factory
        """
        return async_sessionmaker(self.async_engine, expire_on_commit=False)

    @cached_property
    def sync_session_maker(self: "One"):
        """
        Create sync session factory
        """
        return orm.Session(self.sync_engine, expire_on_commit=False)

    async def create_db_and_tables(self):
        """Create all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_async_session(self) -> T.AsyncGenerator[AsyncSession, None]:
        """Dependency for getting async database session."""
        async with self.async_session_maker() as session:
            yield session
