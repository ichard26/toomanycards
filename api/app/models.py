# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import datetime
from typing import Any, Optional
from typing_extensions import Self

import pydantic.fields
from pydantic import BaseModel, Field

Username = str
CardID = str
DeckID = int


class MutableField(pydantic.fields.FieldInfo):
    """A pydantic.fields.FieldInfo subclass that can be updated in-place.

    This is used to make sharing field validation configs easier. This is admittedly hacky.
    """

    def __init__(self, **kwargs: object) -> None:
        # HACK: call Field only for the validation it does.
        Field(**kwargs)
        super().__init__(**kwargs)
        self.__original_kwargs = kwargs

    def __call__(self, **kwargs: object) -> Self:
        final_kwargs = {**self.__original_kwargs, **kwargs}
        return self.__class__(**final_kwargs)

    def keys(self):
        return self.__original_kwargs.keys()

    def __getitem__(self, key: object) -> Any:
        return self.__original_kwargs[key]


class modelfields:
    Username = MutableField(min_length=1, max_length=20, regex=r"^[a-z0-9\.-]+$")
    Password = MutableField(min_length=1, max_length=100)
    DisplayName = MutableField(max_length=50)


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
    display_name: str
    is_admin: bool
    created_at: datetime.datetime
    decks: list[DeckID]


class UserInDB(User):
    hashed_password: str


class AuthSession(BaseModel):
    id: str
    username: str
    refresh_token: str
    refresh_expiry: datetime.datetime
    access_token: str
    access_expiry: datetime.datetime
    created_at: datetime.datetime


class CardTemplate(BaseModel):
    term: str = Field(min_length=1, max_length=50)
    definition: str = Field(min_length=1, max_length=50)
