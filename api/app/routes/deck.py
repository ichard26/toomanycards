# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from fastapi import APIRouter, HTTPException
from florapi import utc_now
from pydantic import BaseModel, Field, validator

from .. import dependencies as deps
from ..models import CardTemplate, Deck, DeckID
from ..models import modelfields as mf

router = APIRouter(prefix="/deck", tags=["deck"])


class DeckTemplate(BaseModel):
    name: str = mf.Deck.Name
    description: str = mf.Deck.Description
    cards: list[CardTemplate]
    public: bool = False

    @validator("cards")
    def cards_length_check(cls, v):
        if (length := len(v)) > 100:
            raise ValueError(f"Deck can only contain up to 100 cards, not {length}")
        return v


class DeckUpdateTemplate(DeckTemplate):
    name: str = mf.Deck.Name(default="")
    description: str = mf.Deck.Description(default="")
    cards: list[CardTemplate] = Field(default_factory=list)


@router.get("/library")
async def get_deck_library(actor: deps.SignedInUser, db: deps.DBConnection) -> list[Deck]:
    return [db.get_deck(id) for id in actor.decks]


@router.post("/new", status_code=201)
async def create_deck(actor: deps.SignedInUser, t: DeckTemplate, db: deps.DBConnection) -> DeckID:
    deck_library = await get_deck_library(actor, db)
    if len(deck_library) >= 50:
        raise HTTPException(400, detail="Reached maximum deck count")

    with db:
        db.insert("decks", {
            "owner": actor.username,
            "name": t.name,
            "description": t.description,
            "created_at": utc_now(), "updated_at": utc_now(), "accessed_at": utc_now(),
            "public": t.public
        })
        deck_id = db.execute("SELECT id FROM decks ORDER BY id DESC LIMIT 1;").fetchone()[0]
        db.insert_many(
            "cards", ("deck_id", "term", "definition"),
            [(deck_id, c.term, c.definition) for c in t.cards]
        )
    return deck_id


@router.get("/{deck_id}")
async def get_deck(actor: deps.MaybeSignedInUser, deck: deps.ExistingDeck) -> Deck:
    if not deck.public:
        if actor is None:
            deps.raise_credentials_error()
        deps.check_for_resource_owner_or_admin(deck.owner, actor)
    return deck


@router.patch("/{deck_id}")
async def update_deck(
    actor: deps.SignedInUser,
    original_deck: deps.ExistingDeck,
    template: DeckUpdateTemplate,
    db: deps.DBConnection,
) -> None:
    """Update a deck. Partial updates are somewhat supported.

    (*) Cards must be replaced with a new complete list at the moment unfortunately.
    """
    deps.check_for_resource_owner_or_admin(original_deck.owner, actor)
    d = original_deck.copy(update=template.dict(exclude_unset=True))
    with db:
        db.delete("cards", {"deck_id": original_deck.id})
        db.update("decks", {
                "name": d.name,
                "description": d.description,
                "updated_at": utc_now(),
                "public": d.public
            },
            where={"id": original_deck.id}
        )
        db.insert_many(
            "cards", ("deck_id", "term", "definition"),
            [(original_deck.id, c.term, c.definition) for c in template.cards]
        )


@router.delete("/{deck_id}")
async def delete_deck(
    actor: deps.SignedInUser, deck: deps.ExistingDeck, db: deps.DBConnection
) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.delete("decks", {"id": deck.id})


@router.post("/{deck_id}/accessed")
async def bump_deck(actor: deps.SignedInUser, deck: deps.ExistingDeck, db: deps.DBConnection) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.update("decks", {"accessed_at": utc_now()}, where={"id": deck.id})
