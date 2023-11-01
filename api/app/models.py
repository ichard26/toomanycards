# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import datetime
from typing import Any, Mapping, Optional, TypeVar
from typing_extensions import Self

import pydantic.fields
from pydantic import BaseModel, Field

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)
Username = str
CardID = str
DeckID = int


def update_model(model: BaseModelT, update: Mapping[str, object], /) -> BaseModelT:
    """Update a model, merging the new contents of another model into it.

    This exists as BaseModel.copy(update=...) does not validate or convert incoming data
    which is problematic.

    Currently not used as the whole data modelling story of this application needs some
    thought first.
    """
    if not model.__config__().validate_assignment:
        raise ValueError(f"unsupported model ({model.__class__.__qualname__}), validate_assigment=True needed")

    new_model = model.copy()
    for field, value in update.items():
        setattr(new_model, field, value)
    return new_model


class ExtensibleField(pydantic.fields.FieldInfo):
    """A pydantic FieldInfo subclass that can be recalled with new parameters.

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
    """Shared model field value validation configuration."""

    Username = ExtensibleField(min_length=1, max_length=20, pattern=r"^[a-z0-9\.-]+$")
    Password = ExtensibleField(min_length=1, max_length=100)
    DisplayName = ExtensibleField(max_length=50)

    class Deck:
        Name = ExtensibleField(min_length=1, max_length=50)
        Description = ExtensibleField(max_length=200)

    class Card:
        Term = ExtensibleField(min_length=1, max_length=50)
        Definition = ExtensibleField(min_length=1, max_length=50)


class Card(BaseModel):
    id: CardID
    term: str
    definition: str


class Deck(BaseModel, validate_assignment=True):
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
    term: str = modelfields.Card.Term
    definition: str = modelfields.Card.Definition
