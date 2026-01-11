# -*- coding: utf-8 -*-

"""
Database configurations.
"""

import typing as T

if T.TYPE_CHECKING:  # pragma: no cover
    from .config_00_main import Env


class DbMixin:
    @property
    def async_db_url(self: "Env") -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.db_user}:{self.db_pass}@{self.db_host}/{self.db_name}"
            f"?sslmode=require&channel_binding=require"
        )
