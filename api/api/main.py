from fastapi import Depends, FastAPI

from .routes import admin, auth, deck

tags_metadata = [
    {"name": "admin", "description": "Administrative operations (**be careful**)."},
    {"name": "auth", "description": "User management and authentication."},
    {"name": "deck", "description": "Deck management."},
]
app = FastAPI(
    title="toomanycards",
    description="The API powering toomanycards, an overengineered Quizlet replacement.",
    contact={"name": "Richard Si"},
    openapi_tags=tags_metadata\
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(deck.router)


@app.get("/")
async def root():
    return {"message": "Welcome to toomanycards's API 🌺."}
