import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware

from .constants import LOG_CONFIG
from .database import open_sqlite_connection
from .routes import admin, auth, deck
from .utils import current_datetime_stamp

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
app.add_middleware(GZipMiddleware, minimum_size=2048)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start_time) * 1000, 2)

    db = open_sqlite_connection()
    try:
        entry = (
            current_datetime_stamp(),
            request.headers.get("User-Agent"),
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        db.execute("""
            INSERT INTO requests(datetime, useragent, verb, path, code, duration)
            VALUES(?, ?, ?, ?, ?, ?);
            """, entry)
        db.commit()
    finally:
        db.close()

    response.headers["Server-Timing"] = f"total;dur={elapsed:.1f}"
    return response


@app.get("/")
async def root():
    return {"message": "Welcome to TooManyCards's API 🌺.", "api-version": __version__}
