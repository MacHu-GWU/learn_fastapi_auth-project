# -*- coding: utf-8 -*-

"""
WebApp configurations.
"""

import typing as T

from ..runtime import runtime

if T.TYPE_CHECKING:  # pragma: no cover
    from .config_00_main import Env


class WebAppMixin:
    @property
    def final_front_end_url(self: "Env") -> str:
        if runtime.is_local_runtime_group:
            return "http://localhost:8000"
        else:
            return s
