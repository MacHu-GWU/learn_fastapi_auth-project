# -*- coding: utf-8 -*-

import asyncio
from learn_fastapi_auth.database import create_db_and_tables

asyncio.run(create_db_and_tables())
