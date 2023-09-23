# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from .. import dependencies as deps
from ..models import CardTemplate, Deck, DeckID
from ..utils import utc_now

router = APIRouter(prefix="/deck", tags=["deck"])


class DeckTemplate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(max_length=200)
    cards: list[CardTemplate]

    @validator("cards")
    def cards_length_check(cls, v):
        if (length := len(v)) > 100:
            raise ValueError(f"Deck can only contain up to 100 cards, not {length}")
        return v


@router.get("/library")
async def get_deck_library(actor: deps.SignedInUser, db: deps.DBConnection) -> list[Deck]:
    return [db.get_deck(id) for id in actor.decks]


@router.post("/new", status_code=201)
async def create_deck(
    actor: deps.SignedInUser, template: DeckTemplate, db: deps.DBConnection
) -> DeckID:
    deck_library = await get_deck_library(actor, db)
    if len(deck_library) >= 50:
        raise HTTPException(400, detail="Reached maximum deck count")

    with db:
        db.insert(
            "decks", ("owner", "name", "description", "created_at", "accessed_at"),
            (actor.username, template.name, template.description, utc_now(), utc_now())
        )
        deck_id = db.execute("SELECT id FROM decks ORDER BY id DESC LIMIT 1;").fetchone()[0]
        db.insert_many(
            "cards", ("deck_id", "term", "definition"),
            [(deck_id, c.term, c.definition) for c in template.cards]
        )
    return deck_id


@router.get("/{deck_id}")
async def get_deck(actor: deps.SignedInUser, deck: deps.ExistingDeck) -> Deck:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    return deck


@router.put("/{deck_id}")
async def replace_deck(
    actor: deps.SignedInUser,
    deck: deps.ExistingDeck,
    t: DeckTemplate,
    db: deps.DBConnection,
) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute("DELETE FROM cards WHERE deck_id = ?;", [deck.id])
        db.execute("DELETE FROM decks WHERE id = ?;", [deck.id])
        db.insert(
            "decks", ("id", "owner", "name", "description", "created_at", "accessed_at"),
            (deck.id, deck.owner, t.name, t.description, deck.created_at, utc_now())
        )
        db.insert_many(
            "cards", ("deck_id", "term", "definition"),
            [(deck.id, c.term, c.definition) for c in t.cards]
        )


@router.delete("/{deck_id}")
async def delete_deck(
    actor: deps.SignedInUser, deck: deps.ExistingDeck, db: deps.DBConnection
) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute("DELETE FROM cards WHERE deck_id = ?;", [deck.id])
        db.execute("DELETE FROM decks WHERE id = ?;", [deck.id])
