from typing import List, Optional

from pydantic import BaseModel

from .database import db

Username = str
CardID = str
DeckID = int


class Card(BaseModel):
    id: CardID
    term: str
    definition: str


class Deck(BaseModel):
    id: DeckID
    owner: Username
    name: str
    description: str
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


def get_deck_from_db(deck_id: int) -> Optional[Deck]:
    decks = db.get("decks")
    if str(deck_id) not in decks:
        return None

    return Deck(**decks[str(deck_id)])
