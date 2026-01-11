# -*- coding: utf-8 -*-

"""
Database configurations.
"""

import typing as T

from ..runtime import runtime
from ..paths import path_enum

if T.TYPE_CHECKING:  # pragma: no cover
    from .config_00_main import Env


class DbMixin:
    @property
    def async_db_url(self: "Env") -> str:
        if runtime.is_local_runtime_group:
            return f"sqlite+aiosqlite:///{path_enum.dir_project_root}/data.db"
        else:
            # Note: asyncpg uses 'ssl' instead of 'sslmode' (libpq style)
            # and doesn't support 'channel_binding'
            return (
                "postgresql+asyncpg://"
                f"{self.db_user}:{self.db_pass}@{self.db_host}/{self.db_name}"
                f"?ssl=require"
            )

    @property
    def sync_db_url(self: "Env") -> str:
        if runtime.is_local_runtime_group:
            return f"sqlite:///{path_enum.dir_project_root}/data.db"
        else:
            # Note: asyncpg uses 'ssl' instead of 'sslmode' (libpq style)
            # and doesn't support 'channel_binding'
            return (
                "postgresql+pg8000://"
                f"{self.db_user}:{self.db_pass}@{self.db_host}/{self.db_name}"
                f"?sslmode=require&channel_binding=require"
            )
