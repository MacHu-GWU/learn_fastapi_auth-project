# -*- coding: utf-8 -*-

"""
WebApp configurations.
"""

import typing as T
import json

from boto_session_manager import BotoSesManager
from simple_aws_ssm_parameter_store.api import get_parameter

from ..runtime import runtime

if T.TYPE_CHECKING:  # pragma: no cover
    from .config_00_main import Env


class WebAppMixin:
    @property
    def final_frontend_url(self: "Env") -> str:
        if runtime.is_local_runtime_group:
            return "http://localhost:3000"
        else:
            return self.frontend_url

    @property
    def firebase_cert_parameter_name(self: "Env") -> str:
        return f"{self.parameter_name}-firebase"

    def get_firebase_cert(self: "Env", bsm: BotoSesManager) -> dict:
        parameter = get_parameter(
            ssm_client=bsm.ssm_client,
            name=self.firebase_cert_parameter_name,
            with_decryption=True,
        )
        return json.loads(parameter.value)
