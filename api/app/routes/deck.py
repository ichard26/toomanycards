from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import dependencies as deps
from ..models import Deck, DeckID
from ..utils import current_datetime_stamp

router = APIRouter(prefix="/deck", tags=["deck"])


class CardTemplate(BaseModel):
    term: str
    definition: str


class DeckTemplate(BaseModel):
    name: str = Field(min_length=1)
    description: str
    cards: list[CardTemplate]


@router.get("/library")
async def get_deck_library(user: deps.SignedInUser, db: deps.DBConnection) -> list[Deck]:
    return [db.get_deck(id) for id in user.decks]


@router.post("/new", status_code=201)
async def create_deck(
    actor: deps.SignedInUser, template: DeckTemplate, db: deps.DBConnection
) -> DeckID:
    with db:
        db.execute(
            "INSERT INTO decks (owner, name, description, created_at) VALUES(?, ?, ?, ?);",
            (actor.username, template.name, template.description, current_datetime_stamp()),
        )
        deck_id = db.execute("SELECT id FROM decks ORDER BY id DESC LIMIT 1;").fetchone()[0]
        db.executemany(
            "INSERT INTO cards (deck_id, term, definition) VALUES(?, ?, ?)",
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
        db.execute(
            "INSERT INTO decks (id, owner, name, description, created_at) VALUES(?, ?, ?, ?, ?);",
            (deck.id, deck.owner, t.name, t.description, deck.created_at),
        )
        db.executemany(
            "INSERT INTO cards (deck_id, term, definition) VALUES(?, ?, ?)",
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
