from typing import List, Optional

from pydantic import BaseModel

from .database import db, fake_users_db

CardID = str
DeckID = int


class Card(BaseModel):
    id: CardID
    term: str
    definition: str


class Deck(BaseModel):
    id: DeckID
    name: str
    cards: List[Card]


class User(BaseModel):
    # Metadata.
    username: str
    full_name: str
    is_admin: bool
    # Data.
    decks: List[DeckID]


class UserInDB(User):
    hashed_password: str


def get_user_from_db(username: str) -> Optional[UserInDB]:
    users = db.get("users")
    if username not in users:
        return None

    return UserInDB(**users[username])
