import datetime
from typing import Optional

from pydantic import BaseModel

Username = str
CardID = str
DeckID = int


class Card(BaseModel):
    id: CardID
    term: str
    definition: str


class Deck(BaseModel):
    id: DeckID
    owner: Optional[Username]
    created_at: str
    name: str
    description: str
    cards: list[Card]


class User(BaseModel):
    username: str
    full_name: str
    is_admin: bool
    created_at: str

    decks: list[DeckID]


class UserInDB(User):
    hashed_password: str


class SignInSession(BaseModel):
    id: str
    username: Username
    created_at: datetime.datetime
    expired_at: datetime.datetime
