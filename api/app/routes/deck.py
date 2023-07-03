from typing import List
from typing_extensions import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

from .. import dependencies as deps
from ..models import Deck, DeckID
from ..utils import current_datetime_stamp

router = APIRouter(prefix="/deck", tags=["deck"])


class NewCard(BaseModel):
    term: str
    definition: str


@router.get("/library")
async def get_deck_library(user: deps.SignedInUser, db: deps.DBConnection) -> List[Deck]:
    return [db.get_deck(id) for id in user.decks]


@router.post("/new", status_code=201)
async def create_deck(
    actor: deps.SignedInUser,
    name: Annotated[str, Body(min_length=1)],
    description: Annotated[str, Body()],
    cards: Annotated[List[NewCard], Body()],
    db: deps.DBConnection,
) -> DeckID:
    with db:
        db.execute(
            "INSERT INTO decks (owner, name, description, created_at) VALUES(?, ?, ?, ?);",
            (actor.username, name, description, current_datetime_stamp()),
        )
        deck_id = db.execute("SELECT id FROM decks ORDER BY id DESC LIMIT 1;").fetchone()[0]
        db.executemany(
            "INSERT INTO cards (deck_id, term, definition) VALUES(?, ?, ?)",
            [(deck_id, c.term, c.definition) for c in cards]
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
    name: Annotated[str, Body(min_length=1)],
    description: Annotated[str, Body()],
    cards: Annotated[List[NewCard], Body()],
    db: deps.DBConnection,
) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute("DELETE FROM cards WHERE deck_id = ?;", [deck.id])
        db.execute("DELETE FROM decks WHERE id = ?;", [deck.id])
        db.execute(
            "INSERT INTO decks (id, owner, name, description, created_at) VALUES(?, ?, ?, ?, ?);",
            (deck.id, deck.owner, name, description, deck.created_at),
        )
        db.executemany(
            "INSERT INTO cards (deck_id, term, definition) VALUES(?, ?, ?)",
            [(deck.id, c.term, c.definition) for c in cards]
        )


@router.delete("/{deck_id}")
async def delete_deck(
    actor: deps.SignedInUser, deck: deps.ExistingDeck, db: deps.DBConnection
) -> None:
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute("DELETE FROM cards WHERE deck_id = ?;", [deck.id])
        db.execute("DELETE FROM decks WHERE id = ?;", [deck.id])
