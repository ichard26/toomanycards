# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import datetime
from typing import Optional

from pydantic import BaseModel, Field

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
    public: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    accessed_at: datetime.datetime
    name: str
    description: str
    cards: list[Card]


class User(BaseModel):
    username: str
    full_name: str
    is_admin: bool
    created_at: datetime.datetime
    decks: list[DeckID]


class UserInDB(User):
    hashed_password: str


class AuthSession(BaseModel):
    username: str
    refresh_token: str
    refresh_expiry: datetime.datetime
    access_token: str
    access_expiry: datetime.datetime
    created_at: datetime.datetime


class CardTemplate(BaseModel):
    term: str = Field(min_length=1, max_length=50)
    definition: str = Field(min_length=1, max_length=50)
