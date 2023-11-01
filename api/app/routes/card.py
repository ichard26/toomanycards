# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from fastapi import APIRouter
from florapi import utc_now
from pydantic import BaseModel

from .. import dependencies as deps
from ..models import modelfields as mf

router = APIRouter(prefix="/card", tags=["deck"])


class CardUpdateTemplate(BaseModel):
    term: str = mf.Card.Term(default="")
    definition: str = mf.Card.Definition(default="")


@router.patch("/{card_id}")
async def update_card(
    actor: deps.SignedInUser,
    card_and_deck: deps.ExistingCard,
    template: CardUpdateTemplate,
    db: deps.DBConnection
) -> None:
    card, deck = card_and_deck
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    card = card.copy(update=template.dict(exclude_unset=True))
    with db:
        db.update("cards", {"term": card.term, "definition": card.definition}, where={"id": card.id})
        db.update("decks", {"updated_at": utc_now()}, where={"id": deck.id})


@router.delete("/{card_id}")
async def delete_card(
    actor: deps.SignedInUser, card_and_deck: deps.ExistingCard, db: deps.DBConnection
) -> None:
    card, deck = card_and_deck
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.delete("cards", {"id": card.id})
        db.update("decks", {"updated_at": utc_now()}, where={"id": deck.id})
