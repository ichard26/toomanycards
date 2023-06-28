from fastapi import FastAPI

from .routes import admin, auth, deck

__version__ = "0.1.0"

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


@app.get("/")
async def root():
    return {"message": "Welcome to TooManyCards's API 🌺.", "api-version": __version__}
