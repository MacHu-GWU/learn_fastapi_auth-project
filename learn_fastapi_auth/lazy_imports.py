# -*- coding: utf-8 -*-

from soft_deps.api import MissingDependency

try:
    import rstobj
except ImportError as e:  # pragma: no cover
    rstobj = MissingDependency(
        name="rstobj",
        error_message=f"please do 'make install-dev'",
    )
