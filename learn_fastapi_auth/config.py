# -*- coding: utf-8 -*-

import os
import dataclasses

from dotenv import load_dotenv


@dataclasses.dataclass
class Config:
    gmail_id: str = dataclasses.field()
    gmail_app_password: str = dataclasses.field()

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            gmail_id=os.environ["GMAIL_ID"],
            gmail_app_password=os.environ["GMAIL_APP_PASSWORD"],
        )


config = Config.from_env()
