from typing import List
from typing_extensions import Annotated
from uuid import uuid4

from fastapi import APIRouter, Body
from pydantic import BaseModel

from .. import dependencies as deps
from ..database import db
from ..models import Deck, get_deck_from_db

router = APIRouter(prefix="/deck", tags=["deck"])


class NewCard(BaseModel):
    term: str
    definition: str


@router.get("/library")
async def get_deck_library(user: deps.SignedInUser) -> List[Deck]:
    return [get_deck_from_db(deck_id) for deck_id in user.decks]


@router.post("/new", status_code=201)
async def create_deck(
    user: deps.SignedInUser,
    name: Annotated[str, Body(min_length=1)],
    description: Annotated[str, Body()],
    cards: Annotated[List[NewCard], Body()],
) -> None:
    decks = db.get("decks")
    new_id = max([int(id) for id in decks] or [0]) + 1
    decks[new_id] = {
        "id": new_id,
        "owner": user.username,
        "name": name,
        "description": description,
        "cards": [{"id": str(uuid4()), "term": c.term, "definition": c.definition} for c in cards],
    }
    db.get("users")[user.username]["decks"].append(new_id)
    db.commit()


@router.get("/{deck_id}")
async def get_deck(actor: deps.SignedInUser, deck: deps.ExistingDeck) -> Deck:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    return deck


@router.put("/{deck_id}")
async def update_deck(deck_id: int):
    return {}


@router.delete("/{deck_id}")
async def delete_deck(actor: deps.SignedInUser, deck: deps.ExistingDeck) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    deck_user = db.get("users")[deck.owner]
    del db.get("decks")[str(deck.id)]
    deck_user["decks"] = [d for d in deck_user["decks"] if deck.id != d]
    db.commit()
