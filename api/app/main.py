# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import time

from fastapi import FastAPI, Request
from starlette.background import BackgroundTask

from .constants import LOG_CONFIG, USE_UNIX_DOMAIN_SOCKET
from .database import open_sqlite_connection
from .routes import admin, auth, deck
from .utils import ProxyHeadersMiddleware, utc_now

__version__ = "0.1.0"

logging.config.dictConfig(LOG_CONFIG)

description = """\
The API powering TooManyCards, an overengineered Quizlet replacement.

**There are absolutely no guarantees on uptime or data security at the moment.**
"""
tags_metadata = [
    {"name": "admin", "description": "Administrative operations (**be careful**)."},
    {"name": "auth", "description": "User management and authentication."},
    {"name": "deck", "description": "Deck management."},
]
app = FastAPI(
    title="TooManyCards API",
    version=__version__,
    description=description,
    contact={"name": "Richard Si"},
    openapi_tags=tags_metadata,
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(deck.router)
app.add_middleware(ProxyHeadersMiddleware, require_none_client=USE_UNIX_DOMAIN_SOCKET)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start_time) * 1000, 2)

    def log() -> None:
        db = open_sqlite_connection()
        try:
            with db:
                db.insert("requests", entry)
        finally:
            db.close()

    entry = {
        "datetime": utc_now(),
        "ip": getattr(request.client, "host", None),
        "useragent": request.headers.get("User-Agent"),
        "verb": request.method,
        "path": request.url.path,
        "code": response.status_code,
        "duration": elapsed,
    }
    response.background = BackgroundTask(log)
    response.headers["Server-Timing"] = f"endpoint;dur={elapsed:.1f}"
    return response


@app.get("/")
async def root():
    return {"message": "Welcome to TooManyCards's API 🌺.", "api-version": __version__}
