# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

__version__ = "0.1.0"

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from florapi.middleware import ProxyHeadersMiddleware, TimedLogMiddleware

from .constants import LOG_CONFIG, USE_UNIX_DOMAIN_SOCKET
from .database import open_sqlite_connection
from .routes import admin, auth, card, deck

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    app.state.log_db = open_sqlite_connection()
    logger.info("Opened SQLite connection for request logging middleware")
    yield
    app.state.log_db.close()
    logger.info("Closed SQLite connection for request logging middleware")


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
    lifespan=lifespan,
    contact={"name": "Richard Si"},
    openapi_tags=tags_metadata,
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(card.router)
app.include_router(deck.router)
app.add_middleware(ProxyHeadersMiddleware, require_none_client=USE_UNIX_DOMAIN_SOCKET)
app.add_middleware(
    TimedLogMiddleware, sqlite_factory=lambda: app.state.log_db, sqlite_autoclose=False
)


@app.get("/")
async def root():
    return {"message": "Welcome to TooManyCards's API 🌺.", "api-version": __version__}
