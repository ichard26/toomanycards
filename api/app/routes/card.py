# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from fastapi import APIRouter

from .. import dependencies as deps
from ..models import CardTemplate
from ..utils import utc_now

router = APIRouter(prefix="/card", tags=["deck"])


@router.put("/{card_id}")
async def replace_card(
    actor: deps.SignedInUser, card_and_deck: deps.ExistingCard, template: CardTemplate, db: deps.DBConnection
) -> None:
    card, deck = card_and_deck
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute(
            "UPDATE cards SET term = ?, definition = ? WHERE id = ?;",
            [template.term, template.definition, card.id]
        )
        db.execute("UPDATE decks SET updated_at = ? WHERE id = ?;", (utc_now(), deck.id))


@router.delete("/{card_id}")
async def delete_card(
    actor: deps.SignedInUser, card_and_deck: deps.ExistingCard, db: deps.DBConnection
) -> None:
    card, deck = card_and_deck
    deps.check_for_resource_owner_or_admin(deck.owner, actor)
    with db:
        db.execute("DELETE FROM cards WHERE id = ?;", [card.id])
        db.execute("UPDATE decks SET updated_at = ? WHERE id = ?;", (utc_now(), deck.id))
